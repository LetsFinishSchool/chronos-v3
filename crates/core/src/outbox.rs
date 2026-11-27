//! Abarbeitung der Outbox (ADR-002, K-003): Das Ereignis wird gelesen, gesperrt, von den
//! Verbrauchern bearbeitet und als verarbeitet markiert, alles in einer Transaktion.

use sqlx::PgPool;
use tracing::{error, warn};

use crate::consumer::{ConsumerError, ConsumerRegistry, OutboxEvent};

/// Nutzt den Teilindex `outbox_pending`. `SKIP LOCKED` lässt Ereignisse aus, die eine andere
/// Worker-Instanz gerade bearbeitet. Der Cursor `id > $1` verhindert, dass ein fehlgeschlagenes
/// Ereignis in derselben Charge sofort wieder an die Reihe kommt.
const NEXT_PENDING_SQL: &str = "SELECT id, event, payload, actor, correlation_id FROM outbox \
     WHERE processed_at IS NULL AND id > $1 \
     ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED";

const MARK_PROCESSED_SQL: &str = "UPDATE outbox SET processed_at = now() WHERE id = $1";

/// Ausgang einer Charge.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct BatchStats {
    /// Als verarbeitet markierte Ereignisse.
    pub processed: u32,
    /// Ereignisse, deren Verbraucher fehlschlug; sie bleiben unverarbeitet.
    pub failed: u32,
}

enum Step {
    NoMoreEvents,
    Processed(i64),
    Failed(i64),
}

/// Datenbankfehler beim Abarbeiten (nicht: Fehler eines Verbrauchers).
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

/// Zugriff des Workers auf die Outbox. Die Datenbank bleibt in `core` (ADR-009): Der Worker
/// kennt nur diesen Rahmen und die Verbraucher.
#[derive(Clone)]
pub struct Outbox {
    pool: PgPool,
}

impl Outbox {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Bearbeitet bis zu `batch_size` Ereignisse in Reihenfolge ihrer `id`. Fehlgeschlagene
    /// Ereignisse zählen nicht mit, bleiben für den nächsten Durchlauf liegen und halten die
    /// Charge nicht auf. Ein Datenbankfehler bricht die Charge ab; bereits festgeschriebene
    /// Ereignisse bleiben verarbeitet.
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
        consumer.handle(event).await?;
    }
    Ok(())
}
