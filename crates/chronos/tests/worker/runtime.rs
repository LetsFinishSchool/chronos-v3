//! Loop, pacing, shutdown and log consumer.

use std::time::Duration;

use chronos_core::{
    Consumer, ConsumerFuture, ConsumerRegistry, Environment, Frame, Outbox, OutboxEvent, Run,
};
use chronos_worker::{LogConsumer, WorkerConfig, run};
use sqlx::PgPool;
use tokio_util::sync::CancellationToken;
use tracing::instrument::WithSubscriber;
use uuid::Uuid;

use super::beispiel::SETUP_SQL;
use super::support::{LogBuffer, insert_event, is_processed, processed_count};

const WAIT_LIMIT: Duration = Duration::from_secs(10);
/// So long that only a stop signal or a full batch moves the loop on.
const NEVER: Duration = Duration::from_secs(3600);

fn config(poll_interval: Duration, batch_size: u32) -> WorkerConfig {
    WorkerConfig {
        poll_interval,
        batch_size: batch_size.try_into().unwrap(),
    }
}

async fn wait_for_processed(pool: &PgPool, expected: i64) {
    tokio::time::timeout(WAIT_LIMIT, async {
        while processed_count(pool).await < expected {
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await
    .expect("the worker processes the events in time");
}

async fn stop(worker: tokio::task::JoinHandle<()>, token: &CancellationToken) {
    token.cancel();
    tokio::time::timeout(WAIT_LIMIT, worker)
        .await
        .expect("the worker stops in time")
        .unwrap();
}

/// Triggers the stop while the first event of the batch is running.
struct StopDuringBatch(CancellationToken);

impl Consumer for StopDuringBatch {
    fn handle<'a>(&'a self, _: &'a OutboxEvent) -> ConsumerFuture<'a> {
        self.0.cancel();
        Box::pin(async { Ok(()) })
    }
}

#[sqlx::test]
async fn polling_picks_up_events_that_arrive_later(pool: PgPool) {
    let mut registry = ConsumerRegistry::new();
    registry.register("a.happened", LogConsumer);
    let token = CancellationToken::new();
    let worker = tokio::spawn({
        let (pool, token) = (pool.clone(), token.clone());
        async move {
            run(
                &Outbox::new(pool.clone()),
                &registry,
                &config(Duration::from_millis(20), 50),
                token,
            )
            .await;
        }
    });

    let id = insert_event(&pool, "a.happened").await;
    wait_for_processed(&pool, 1).await;

    assert!(is_processed(&pool, id).await);
    stop(worker, &token).await;
}

#[sqlx::test]
async fn a_full_batch_is_followed_by_the_next_without_a_pause(pool: PgPool) {
    for _ in 0..5 {
        insert_event(&pool, "a.happened").await;
    }
    let mut registry = ConsumerRegistry::new();
    registry.register("a.happened", LogConsumer);
    let token = CancellationToken::new();
    let worker = tokio::spawn({
        let (pool, token) = (pool.clone(), token.clone());
        // With batch size 2 this takes three batches; after the third (not full) the loop
        // waits an hour.
        async move {
            run(
                &Outbox::new(pool.clone()),
                &registry,
                &config(NEVER, 2),
                token,
            )
            .await
        }
    });

    wait_for_processed(&pool, 5).await;

    stop(worker, &token).await;
}

#[sqlx::test]
async fn shutdown_finishes_the_running_batch(pool: PgPool) {
    let ids = [
        insert_event(&pool, "a.happened").await,
        insert_event(&pool, "a.happened").await,
        insert_event(&pool, "a.happened").await,
    ];
    let token = CancellationToken::new();
    let mut registry = ConsumerRegistry::new();
    registry.register("a.happened", StopDuringBatch(token.clone()));

    tokio::time::timeout(
        WAIT_LIMIT,
        run(
            &Outbox::new(pool.clone()),
            &registry,
            &config(NEVER, 50),
            token.clone(),
        ),
    )
    .await
    .expect("run returns after the batch");

    for id in ids {
        assert!(is_processed(&pool, id).await, "event {id} was left behind");
    }
}

#[sqlx::test]
async fn shutdown_interrupts_the_pause_between_batches(pool: PgPool) {
    let token = CancellationToken::new();
    let worker = tokio::spawn({
        let (pool, token) = (pool.clone(), token.clone());
        async move {
            run(
                &Outbox::new(pool.clone()),
                &ConsumerRegistry::new(),
                &config(NEVER, 50),
                token,
            )
            .await
        }
    });
    tokio::time::sleep(Duration::from_millis(100)).await;

    stop(worker, &token).await;
}

#[sqlx::test]
async fn an_example_operation_event_shows_up_in_the_worker_log_with_its_correlation_id(
    pool: PgPool,
) {
    sqlx::query(SETUP_SQL).execute(&pool).await.unwrap();
    let frame = Frame::new(pool.clone(), Environment::Test);
    let principal = frame.test_principal().await.unwrap();
    let correlation_id = Uuid::new_v4();
    frame
        .execute(
            &principal,
            "notes.create",
            serde_json::json!({ "owner": principal.id(), "text": "Hello" }),
            correlation_id,
            Run::Apply,
        )
        .await
        .unwrap();
    let mut registry = ConsumerRegistry::new();
    registry.register("note.created", LogConsumer);
    let (logs, subscriber) = LogBuffer::subscriber();

    Outbox::new(pool.clone())
        .process_batch(&registry, 50)
        .with_subscriber(subscriber)
        .await
        .unwrap();

    let received: Vec<_> = logs
        .lines()
        .into_iter()
        .filter(|line| line["fields"]["message"] == "outbox event received")
        .collect();
    assert_eq!(received.len(), 1, "{received:?}");
    let fields = &received[0]["fields"];
    assert_eq!(fields["event"], "note.created");
    assert_eq!(fields["correlation_id"], correlation_id.to_string());
    assert_eq!(fields["actor"], principal.id().uuid().to_string());
}
