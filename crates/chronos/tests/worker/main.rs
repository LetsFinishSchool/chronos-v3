//! Worker tests (#102, K-003) against real PostgreSQL.
//! Requires `docker compose up --wait` and `DATABASE_URL`.

#[path = "../operationsrahmen/beispiel.rs"]
mod beispiel;
mod runtime;
mod support;

use std::sync::Arc;
use std::sync::atomic::{AtomicU32, Ordering};
use std::time::Duration;

use chronos_core::{
    Consumer, ConsumerError, ConsumerFuture, ConsumerRegistry, Outbox, OutboxEvent,
};
use sqlx::PgPool;
use tokio::sync::Notify;

use support::{LogBuffer, insert_event, is_processed, processed_count};

const BATCH: u32 = 50;

/// Holds an event in its transaction until the test releases it.
struct Blocking {
    started: Arc<Notify>,
    release: Arc<Notify>,
}

impl Consumer for Blocking {
    fn handle<'a>(&'a self, _: &'a OutboxEvent) -> ConsumerFuture<'a> {
        Box::pin(async move {
            self.started.notify_one();
            self.release.notified().await;
            Ok(())
        })
    }
}

/// Remembers every handled event `id`.
#[derive(Clone, Default)]
struct Recording(Arc<std::sync::Mutex<Vec<i64>>>);

impl Recording {
    fn ids(&self) -> Vec<i64> {
        let mut ids = self.0.lock().unwrap().clone();
        ids.sort_unstable();
        ids
    }
}

impl Consumer for Recording {
    fn handle<'a>(&'a self, event: &'a OutboxEvent) -> ConsumerFuture<'a> {
        Box::pin(async move {
            self.0.lock().unwrap().push(event.id);
            tokio::task::yield_now().await;
            Ok(())
        })
    }
}

/// Fails the first `failures` calls and counts all calls.
struct Flaky {
    failures: AtomicU32,
    calls: Arc<AtomicU32>,
}

impl Consumer for Flaky {
    fn handle<'a>(&'a self, _: &'a OutboxEvent) -> ConsumerFuture<'a> {
        Box::pin(async move {
            self.calls.fetch_add(1, Ordering::SeqCst);
            let remaining = self.failures.load(Ordering::SeqCst);
            if remaining > 0 {
                self.failures.store(remaining - 1, Ordering::SeqCst);
                return Err(ConsumerError::from("intentional failure"));
            }
            Ok(())
        })
    }
}

struct Panicking;

impl Consumer for Panicking {
    fn handle<'a>(&'a self, _: &'a OutboxEvent) -> ConsumerFuture<'a> {
        panic!("intentional panic");
    }
}

mod processing {
    use super::*;

    #[sqlx::test]
    async fn processes_events_in_order_and_marks_them(pool: PgPool) {
        let ids = [
            insert_event(&pool, "a.happened").await,
            insert_event(&pool, "a.happened").await,
            insert_event(&pool, "a.happened").await,
        ];
        let recording = Recording::default();
        let mut registry = ConsumerRegistry::new();
        registry.register("a.happened", recording.clone());

        let stats = Outbox::new(pool.clone())
            .process_batch(&registry, BATCH)
            .await
            .unwrap();

        assert_eq!((stats.processed, stats.failed), (3, 0));
        assert_eq!(recording.ids(), ids);
        assert_eq!(processed_count(&pool).await, 3);
    }

    #[sqlx::test]
    async fn batch_size_limits_one_batch(pool: PgPool) {
        for _ in 0..5 {
            insert_event(&pool, "a.happened").await;
        }
        let mut registry = ConsumerRegistry::new();
        registry.register("a.happened", Recording::default());

        let first = Outbox::new(pool.clone())
            .process_batch(&registry, 2)
            .await
            .unwrap();
        assert_eq!(first.processed, 2);
        assert_eq!(processed_count(&pool).await, 2);

        let rest = Outbox::new(pool.clone())
            .process_batch(&registry, 10)
            .await
            .unwrap();
        assert_eq!(rest.processed, 3);
        assert_eq!(processed_count(&pool).await, 5);
    }

    #[sqlx::test]
    async fn event_without_consumer_is_processed_with_a_warning(pool: PgPool) {
        let unknown = insert_event(&pool, "nobody.listens").await;
        let known = insert_event(&pool, "a.happened").await;
        let recording = Recording::default();
        let mut registry = ConsumerRegistry::new();
        registry.register("a.happened", recording.clone());

        let (logs, subscriber) = LogBuffer::subscriber();
        let stats = tracing::instrument::WithSubscriber::with_subscriber(
            Outbox::new(pool.clone()).process_batch(&registry, BATCH),
            subscriber,
        )
        .await
        .unwrap();

        assert_eq!((stats.processed, stats.failed), (2, 0));
        assert!(is_processed(&pool, unknown).await);
        assert!(is_processed(&pool, known).await);
        assert_eq!(recording.ids(), [known]);
        let warnings: Vec<_> = logs
            .lines()
            .into_iter()
            .filter(|line| line["level"] == "WARN")
            .collect();
        assert_eq!(warnings.len(), 1, "{warnings:?}");
        assert_eq!(warnings[0]["fields"]["event"], "nobody.listens");
        assert_eq!(warnings[0]["fields"]["event_id"], unknown);
    }

    #[sqlx::test]
    async fn failing_consumer_leaves_the_event_unprocessed_and_the_next_batch_retries(
        pool: PgPool,
    ) {
        let failing = insert_event(&pool, "b.happened").await;
        let healthy = insert_event(&pool, "a.happened").await;
        let recording = Recording::default();
        let mut registry = ConsumerRegistry::new();
        let calls = Arc::new(AtomicU32::new(0));
        registry.register(
            "b.happened",
            Flaky {
                failures: AtomicU32::new(1),
                calls: calls.clone(),
            },
        );
        registry.register("a.happened", recording.clone());

        let (logs, subscriber) = LogBuffer::subscriber();
        let first = tracing::instrument::WithSubscriber::with_subscriber(
            Outbox::new(pool.clone()).process_batch(&registry, BATCH),
            subscriber,
        )
        .await
        .unwrap();

        // The event behind it is handled anyway.
        assert_eq!((first.processed, first.failed), (1, 1));
        assert!(!is_processed(&pool, failing).await);
        assert!(is_processed(&pool, healthy).await);
        let errors: Vec<_> = logs
            .lines()
            .into_iter()
            .filter(|line| line["level"] == "ERROR")
            .collect();
        assert_eq!(errors.len(), 1, "{errors:?}");
        assert_eq!(errors[0]["fields"]["event_id"], failing);
        assert!(errors[0]["fields"]["correlation_id"].is_string());

        let second = Outbox::new(pool.clone())
            .process_batch(&registry, BATCH)
            .await
            .unwrap();

        assert_eq!((second.processed, second.failed), (1, 0));
        assert!(is_processed(&pool, failing).await);
        assert_eq!(
            calls.load(Ordering::SeqCst),
            2,
            "tried again in the next batch"
        );
    }

    #[sqlx::test]
    async fn panicking_consumer_counts_as_a_failure(pool: PgPool) {
        let panicking = insert_event(&pool, "p.happened").await;
        let healthy = insert_event(&pool, "a.happened").await;
        let mut registry = ConsumerRegistry::new();
        registry.register("p.happened", Panicking);
        registry.register("a.happened", Recording::default());

        let stats = Outbox::new(pool.clone())
            .process_batch(&registry, BATCH)
            .await
            .unwrap();

        assert_eq!((stats.processed, stats.failed), (1, 1));
        assert!(!is_processed(&pool, panicking).await);
        assert!(is_processed(&pool, healthy).await);
    }

    #[sqlx::test]
    async fn aborted_worker_loses_nothing_and_marks_the_event_once(pool: PgPool) {
        let id = insert_event(&pool, "a.happened").await;
        let started = Arc::new(Notify::new());
        let mut crashing = ConsumerRegistry::new();
        crashing.register(
            "a.happened",
            Blocking {
                started: started.clone(),
                release: Arc::new(Notify::new()),
            },
        );

        // The worker read and locked the event but never marks it.
        let worker = tokio::spawn({
            let pool = pool.clone();
            async move {
                Outbox::new(pool.clone())
                    .process_batch(&crashing, BATCH)
                    .await
            }
        });
        started.notified().await;
        worker.abort();
        let _ = worker.await;

        let recording = Recording::default();
        let mut restarted = ConsumerRegistry::new();
        restarted.register("a.happened", recording.clone());
        // The abort drops the transaction; the lock is released once sqlx has rolled it back.
        let mut processed = 0;
        for _ in 0..100 {
            processed = Outbox::new(pool.clone())
                .process_batch(&restarted, BATCH)
                .await
                .unwrap()
                .processed;
            if processed > 0 {
                break;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }

        assert_eq!(processed, 1);
        assert_eq!(recording.ids(), [id]);
        assert!(is_processed(&pool, id).await);
        assert_eq!(processed_count(&pool).await, 1);
        let again = Outbox::new(pool.clone())
            .process_batch(&restarted, BATCH)
            .await
            .unwrap();
        assert_eq!(again.processed, 0);
        assert_eq!(recording.ids(), [id], "the event is not handled twice");
    }

    #[sqlx::test]
    async fn a_second_worker_skips_events_the_first_one_holds(pool: PgPool) {
        let held = insert_event(&pool, "a.happened").await;
        let others = [
            insert_event(&pool, "a.happened").await,
            insert_event(&pool, "a.happened").await,
        ];
        let started = Arc::new(Notify::new());
        let release = Arc::new(Notify::new());
        let mut first = ConsumerRegistry::new();
        first.register(
            "a.happened",
            Blocking {
                started: started.clone(),
                release: release.clone(),
            },
        );
        let first_worker = tokio::spawn({
            let pool = pool.clone();
            async move { Outbox::new(pool.clone()).process_batch(&first, BATCH).await }
        });
        started.notified().await;

        let recording = Recording::default();
        let mut second = ConsumerRegistry::new();
        second.register("a.happened", recording.clone());
        let stats = Outbox::new(pool.clone())
            .process_batch(&second, BATCH)
            .await
            .unwrap();

        assert_eq!(stats.processed, 2);
        assert_eq!(recording.ids(), others);
        assert!(!is_processed(&pool, held).await);

        // The first worker's event only waits for its release; the second worker has
        // meanwhile handled the other two.
        for _ in 0..3 {
            release.notify_one();
        }
        let first_stats = first_worker.await.unwrap().unwrap();
        assert_eq!(first_stats.processed, 1);
        assert_eq!(processed_count(&pool).await, 3);
    }

    #[sqlx::test]
    async fn concurrent_workers_never_handle_the_same_event_twice(pool: PgPool) {
        for _ in 0..200 {
            insert_event(&pool, "a.happened").await;
        }
        let recording = Recording::default();
        let mut registry = ConsumerRegistry::new();
        registry.register("a.happened", recording.clone());

        let workers: Vec<_> = (0..3)
            .map(|_| {
                let pool = pool.clone();
                let registry = registry.clone();
                tokio::spawn(async move {
                    let mut total = 0;
                    loop {
                        let stats = Outbox::new(pool.clone())
                            .process_batch(&registry, 7)
                            .await
                            .unwrap();
                        if stats.processed == 0 {
                            return total;
                        }
                        total += stats.processed;
                    }
                })
            })
            .collect();
        let mut sum = 0;
        for worker in workers {
            sum += worker.await.unwrap();
        }

        let ids = recording.ids();
        let mut unique = ids.clone();
        unique.dedup();
        assert_eq!(ids, unique, "an event was handled twice");
        assert_eq!(sum, 200);
        assert_eq!(ids.len(), 200);
        assert_eq!(processed_count(&pool).await, 200);
    }
}
