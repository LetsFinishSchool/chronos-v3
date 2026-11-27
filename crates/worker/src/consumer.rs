//! Verbraucher von Outbox-Ereignissen und ihre Registrierung je Ereignisart (K-003).

use std::collections::HashMap;
use std::pin::Pin;
use std::sync::Arc;

use serde_json::Value;
use sqlx::{FromRow, PgConnection};
use uuid::Uuid;

/// Ein Ereignis aus der Outbox, wie der Rahmen es festgehalten hat.
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

/// Ergebnis eines Verbraucheraufrufs. Ein Trait-Objekt braucht den Box-Typ, `async fn` im
/// Trait ist nicht objektsicher.
pub type ConsumerFuture<'a> = Pin<Box<dyn Future<Output = Result<(), ConsumerError>> + Send + 'a>>;

/// Reagiert auf ein Ereignis. Der Aufruf läuft in derselben Transaktion, die das Ereignis
/// als verarbeitet markiert: Datenbankänderungen über `connection` werden mit der Markierung
/// festgeschrieben oder zusammen mit ihr zurückgerollt.
///
/// Der Aufruf kann nach einem Absturz wiederholt werden; Seiteneffekte außerhalb der
/// Datenbank (Log, Zustellung) müssen das aushalten.
pub trait Consumer: Send + Sync {
    /// Ein `Err` rollt die Transaktion zurück, das Ereignis bleibt unverarbeitet.
    fn handle<'a>(
        &'a self,
        event: &'a OutboxEvent,
        connection: &'a mut PgConnection,
    ) -> ConsumerFuture<'a>;
}

/// Verbraucher je Ereignisart. Mehrere für dieselbe Art laufen nacheinander in einer
/// Transaktion.
#[derive(Clone, Default)]
pub struct Registry {
    consumers: HashMap<String, Vec<Arc<dyn Consumer>>>,
}

impl Registry {
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
