//! Consumers of outbox events and their registration per event type (K-003).

use std::collections::HashMap;
use std::pin::Pin;
use std::sync::Arc;

use serde_json::Value;
use sqlx::FromRow;
use uuid::Uuid;

/// An event from the outbox as the frame recorded it.
#[derive(Clone, Debug, FromRow)]
pub struct OutboxEvent {
    pub id: i64,
    #[sqlx(rename = "event")]
    pub name: String,
    pub payload: Value,
    pub actor: Uuid,
    pub correlation_id: Uuid,
}

pub type ConsumerError = Box<dyn std::error::Error + Send + Sync>;

/// Result of a consumer call. A trait object needs the boxed type; `async fn` in traits is
/// not object safe.
pub type ConsumerFuture<'a> = Pin<Box<dyn Future<Output = Result<(), ConsumerError>> + Send + 'a>>;

/// Reacts to an event. The call runs while the event is locked; only after an `Ok` does the
/// frame mark it as processed in the same transaction.
///
/// The call may be repeated after a crash, so side effects (log, delivery) must tolerate
/// that. Data changes go through operations, never around the frame, which is why the
/// consumer gets no database connection.
pub trait Consumer: Send + Sync {
    /// An `Err` rolls the transaction back; the event stays unprocessed.
    fn handle<'a>(&'a self, event: &'a OutboxEvent) -> ConsumerFuture<'a>;
}

/// Consumers per event type. Several for the same type run one after another in one
/// transaction.
#[derive(Clone, Default)]
pub struct ConsumerRegistry {
    consumers: HashMap<String, Vec<Arc<dyn Consumer>>>,
}

impl ConsumerRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(
        &mut self,
        event_name: impl Into<String>,
        consumer: impl Consumer + 'static,
    ) -> &mut Self {
        self.consumers
            .entry(event_name.into())
            .or_default()
            .push(Arc::new(consumer));
        self
    }

    pub(crate) fn consumers_for(&self, event_name: &str) -> &[Arc<dyn Consumer>] {
        self.consumers.get(event_name).map_or(&[], Vec::as_slice)
    }
}
