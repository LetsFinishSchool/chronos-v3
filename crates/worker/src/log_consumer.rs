//! First consumer: only writes a structured log entry (#102).

use chronos_core::{Consumer, ConsumerFuture, OutboxEvent};
use tracing::info;

/// Proves that events from the web process arrive in the worker. The payload is kept out of
/// the log on purpose (K-009: no unnecessary personal data).
pub struct LogConsumer;

impl Consumer for LogConsumer {
    fn handle<'a>(&'a self, event: &'a OutboxEvent) -> ConsumerFuture<'a> {
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
