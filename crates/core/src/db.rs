//! Datenbankanbindung: Verbindungspool und Prüfung der Schemaversion (ADR-003, ADR-011).
//!
//! Web und Worker führen keine Migrationen aus. Sie warten beim Start, bis das Schema
//! die Version des Binarys erreicht hat (Punkt 3 in ADR-011).

use std::time::Duration;

use sqlx::PgPool;
use sqlx::migrate::Migrator;
use sqlx::postgres::PgPoolOptions;
use tokio::time::{Instant, sleep};

const MAX_CONNECTIONS: u32 = 10;
const ACQUIRE_TIMEOUT: Duration = Duration::from_secs(5);
const POLL_INTERVAL: Duration = Duration::from_secs(1);

/// Standardwartezeit auf die Schemaversion beim Start.
pub const DEFAULT_SCHEMA_WAIT: Duration = Duration::from_secs(60);

/// Öffnet den Verbindungspool.
pub async fn connect(url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(MAX_CONNECTIONS)
        .acquire_timeout(ACQUIRE_TIMEOUT)
        .connect(url)
        .await
}

/// Wie [`connect`], baut die erste Verbindung aber erst bei Bedarf auf. So kann
/// [`wait_for_schema`] eine noch nicht erreichbare Datenbank abwarten.
pub fn connect_lazy(url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(MAX_CONNECTIONS)
        .acquire_timeout(ACQUIRE_TIMEOUT)
        .connect_lazy(url)
}

/// Neueste Version, die das Binary kennt; `0`, wenn es keine Migration enthält.
pub fn required_version(migrator: &Migrator) -> i64 {
    migrator.iter().map(|m| m.version).max().unwrap_or(0)
}

/// Neueste vollständig eingespielte Version; `None`, wenn noch nichts eingespielt ist.
pub async fn applied_version(pool: &PgPool) -> Result<Option<i64>, sqlx::Error> {
    let table_exists: bool =
        sqlx::query_scalar("SELECT to_regclass('_sqlx_migrations') IS NOT NULL")
            .fetch_one(pool)
            .await?;
    if !table_exists {
        return Ok(None);
    }
    sqlx::query_scalar("SELECT max(version) FROM _sqlx_migrations WHERE success")
        .fetch_one(pool)
        .await
}

/// Warum die Schemaversion nicht passt.
#[derive(Debug)]
pub enum SchemaError {
    /// Die Datenbank blieb hinter dem Binary zurück, bis die Wartezeit ablief.
    Outdated {
        required: i64,
        applied: Option<i64>,
        waited: Duration,
    },
    /// Die Datenbank war bis zum Ablauf der Wartezeit nicht erreichbar oder nicht lesbar.
    Unavailable {
        source: sqlx::Error,
        waited: Duration,
    },
}

impl std::fmt::Display for SchemaError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Outdated {
                required,
                applied,
                waited,
            } => {
                let state = applied.map_or_else(
                    || "Es ist noch keine Migration eingespielt".to_owned(),
                    |version| format!("Die Schemaversion ist {version}"),
                );
                write!(
                    f,
                    "{state}, das Binary benötigt mindestens {required} (nach {}s Wartezeit). \
                     `chronos migrate` ausführen oder auf den Migrationsjob warten.",
                    waited.as_secs()
                )
            }
            Self::Unavailable { source, waited } => write!(
                f,
                "Schemaversion nicht lesbar (nach {}s Wartezeit): {source}",
                waited.as_secs()
            ),
        }
    }
}

impl std::error::Error for SchemaError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Outdated { .. } => None,
            Self::Unavailable { source, .. } => Some(source),
        }
    }
}

/// Wartet, bis die Datenbank mindestens die Schemaversion des Binarys hat.
///
/// Eine weiter fortgeschrittene Datenbank ist erlaubt: alte und neue Version laufen
/// beim Rollout kurz nebeneinander (ADR-011, Punkt 6).
pub async fn wait_for_schema(
    pool: &PgPool,
    migrator: &Migrator,
    max_wait: Duration,
) -> Result<(), SchemaError> {
    wait_for_schema_polling(pool, migrator, max_wait, POLL_INTERVAL).await
}

async fn wait_for_schema_polling(
    pool: &PgPool,
    migrator: &Migrator,
    max_wait: Duration,
    poll_interval: Duration,
) -> Result<(), SchemaError> {
    let required = required_version(migrator);
    let started = Instant::now();
    loop {
        let outcome = applied_version(pool).await;
        let waited = started.elapsed();
        let timed_out = waited >= max_wait;
        match outcome {
            Ok(applied) if applied.unwrap_or(0) >= required => return Ok(()),
            Ok(applied) if timed_out => {
                return Err(SchemaError::Outdated {
                    required,
                    applied,
                    waited,
                });
            }
            Err(source) if timed_out => return Err(SchemaError::Unavailable { source, waited }),
            _ => sleep(poll_interval).await,
        }
    }
}
