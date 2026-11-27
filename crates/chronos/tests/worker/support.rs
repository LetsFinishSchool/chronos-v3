//! Hilfen der Worker-Tests: Ereignisse anlegen, Zustand lesen, Log mitschneiden.

use std::io;
use std::sync::{Arc, Mutex};

use serde_json::{Value, json};
use sqlx::PgPool;
use tracing_subscriber::fmt::MakeWriter;

pub async fn insert_event(pool: &PgPool, name: &str) -> i64 {
    insert_event_with(pool, name, uuid::Uuid::new_v4()).await
}

pub async fn insert_event_with(pool: &PgPool, name: &str, correlation_id: uuid::Uuid) -> i64 {
    let actor: uuid::Uuid =
        sqlx::query_scalar("INSERT INTO person (kind) VALUES ('person') RETURNING id")
            .fetch_one(pool)
            .await
            .unwrap();
    sqlx::query_scalar(
        "INSERT INTO outbox (event, payload, actor, correlation_id) \
         VALUES ($1, $2, $3, $4) RETURNING id",
    )
    .bind(name)
    .bind(json!({}))
    .bind(actor)
    .bind(correlation_id)
    .fetch_one(pool)
    .await
    .unwrap()
}

pub async fn is_processed(pool: &PgPool, id: i64) -> bool {
    sqlx::query_scalar("SELECT processed_at IS NOT NULL FROM outbox WHERE id = $1")
        .bind(id)
        .fetch_one(pool)
        .await
        .unwrap()
}

pub async fn processed_count(pool: &PgPool) -> i64 {
    sqlx::query_scalar("SELECT count(*) FROM outbox WHERE processed_at IS NOT NULL")
        .fetch_one(pool)
        .await
        .unwrap()
}

/// Schneidet strukturierte Log-Zeilen (JSON) in den Speicher mit.
#[derive(Clone, Default)]
pub struct LogBuffer(Arc<Mutex<Vec<u8>>>);

impl LogBuffer {
    pub fn subscriber() -> (Self, impl tracing::Subscriber + Send + Sync) {
        let buffer = Self::default();
        let subscriber = tracing_subscriber::fmt()
            .json()
            .with_ansi(false)
            .with_writer(buffer.clone())
            .finish();
        (buffer, subscriber)
    }

    pub fn lines(&self) -> Vec<Value> {
        let bytes = self.0.lock().unwrap().clone();
        String::from_utf8(bytes)
            .unwrap()
            .lines()
            .map(|line| serde_json::from_str(line).unwrap())
            .collect()
    }
}

impl io::Write for LogBuffer {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.0.lock().unwrap().extend_from_slice(buf);
        Ok(buf.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

impl<'a> MakeWriter<'a> for LogBuffer {
    type Writer = Self;

    fn make_writer(&'a self) -> Self::Writer {
        self.clone()
    }
}
