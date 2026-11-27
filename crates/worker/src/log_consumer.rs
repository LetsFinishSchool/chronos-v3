//! Erster Verbraucher: schreibt nur ein strukturiertes Log (#102).

use sqlx::PgConnection;
use tracing::info;

use crate::consumer::{Consumer, ConsumerFuture, OutboxEvent};

/// Belegt, dass Ereignisse aus dem Web-Prozess im Worker ankommen. Die Nutzdaten bleiben
/// bewusst aus dem Log (K-009: keine unnötigen personenbezogenen Daten).
pub struct LogConsumer;

impl Consumer for LogConsumer {
    fn handle<'a>(
        &'a self,
        event: &'a OutboxEvent,
        _connection: &'a mut PgConnection,
    ) -> ConsumerFuture<'a> {
        info!(
            event_id = event.id,
            event = %event.name,
            actor = %event.actor,
            correlation_id = %event.correlation_id,
            "outbox event received",
        );
        Box::pin(async { Ok(()) })
    }
}
