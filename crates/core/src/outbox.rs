//! Outbox processing (ADR-002, K-003): the event is read, locked, handled by the consumers
//! and marked as processed, all in one transaction.

use std::sync::Arc;

use sqlx::PgPool;
use tracing::instrument::WithSubscriber;
use tracing::{error, warn};

use crate::consumer::{ConsumerError, ConsumerRegistry, OutboxEvent};

/// Uses the partial index `outbox_pending`. `SKIP LOCKED` skips events another worker
/// instance is handling. The cursor `id > $1` keeps a failed event from coming up again
/// right away in the same batch.
const NEXT_PENDING_SQL: &str = "SELECT id, event, payload, actor, correlation_id FROM outbox \
     WHERE processed_at IS NULL AND id > $1 \
     ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED";

const MARK_PROCESSED_SQL: &str = "UPDATE outbox SET processed_at = now() WHERE id = $1";

/// Outcome of a batch.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct BatchStats {
    /// Events marked as processed.
    pub processed: u32,
    /// Events whose consumer failed; they stay unprocessed.
    pub failed: u32,
}

enum Step {
    NoMoreEvents,
    Processed(i64),
    Failed(i64),
}

/// Database error while processing (not a consumer error).
#[derive(Debug)]
pub struct OutboxError(sqlx::Error);

impl std::fmt::Display for OutboxError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}

impl std::error::Error for OutboxError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        Some(&self.0)
    }
}

impl From<sqlx::Error> for OutboxError {
    fn from(error: sqlx::Error) -> Self {
        Self(error)
    }
}

/// The worker's access to the outbox. The database stays in `core` (ADR-009): the worker
/// only knows this frame and the consumers.
#[derive(Clone)]
pub struct Outbox {
    pool: PgPool,
}

impl Outbox {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Handles up to `batch_size` events in `id` order. Failed events do not count, stay for
    /// the next run and do not hold up the batch. A database error aborts the batch; events
    /// already committed stay processed.
    pub async fn process_batch(
        &self,
        registry: &ConsumerRegistry,
        batch_size: u32,
    ) -> Result<BatchStats, OutboxError> {
        let mut stats = BatchStats::default();
        let mut after = 0;
        while stats.processed < batch_size {
            match process_next(&self.pool, registry, after).await? {
                Step::NoMoreEvents => break,
                Step::Processed(id) => {
                    stats.processed += 1;
                    after = id;
                }
                Step::Failed(id) => {
                    stats.failed += 1;
                    after = id;
                }
            }
        }
        Ok(stats)
    }
}

async fn process_next(
    pool: &PgPool,
    registry: &ConsumerRegistry,
    after: i64,
) -> Result<Step, sqlx::Error> {
    let mut transaction = pool.begin().await?;
    let Some(event) = sqlx::query_as::<_, OutboxEvent>(NEXT_PENDING_SQL)
        .bind(after)
        .fetch_optional(&mut *transaction)
        .await?
    else {
        return Ok(Step::NoMoreEvents);
    };

    if let Err(source) = run_consumers(registry, &event).await {
        error!(
            event_id = event.id,
            event = %event.name,
            correlation_id = %event.correlation_id,
            error = %source,
            "consumer failed; event stays unprocessed",
        );
        transaction.rollback().await?;
        return Ok(Step::Failed(event.id));
    }

    sqlx::query(MARK_PROCESSED_SQL)
        .bind(event.id)
        .execute(&mut *transaction)
        .await?;
    transaction.commit().await?;
    Ok(Step::Processed(event.id))
}

/// Each consumer runs in its own task: a panic counts like an `Err`, so a single event
/// cannot crash the worker again on every restart.
async fn run_consumers(
    registry: &ConsumerRegistry,
    event: &OutboxEvent,
) -> Result<(), ConsumerError> {
    let consumers = registry.consumers_for(&event.name);
    if consumers.is_empty() {
        warn!(
            event_id = event.id,
            event = %event.name,
            correlation_id = %event.correlation_id,
            "no consumer registered; event marked as processed",
        );
    }
    for consumer in consumers {
        let consumer = Arc::clone(consumer);
        let event = event.clone();
        tokio::spawn(async move { consumer.handle(&event).await }.with_current_subscriber())
            .await
            .map_err(|panic| ConsumerError::from(format!("consumer panicked: {panic}")))??;
    }
    Ok(())
}
