//! Einstiegspunkt: ein Binary mit Unterbefehlen für alle Prozesse (ADR-002, ADR-011).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use std::num::NonZeroU32;
use std::process::ExitCode;
use std::time::Duration;

use chronos_core::db::{self, SchemaError};
use chronos_core::{ConsumerRegistry, Outbox};
use chronos_worker::WorkerConfig;
use clap::{Parser, Subcommand};
use sqlx::PgPool;
use sqlx::migrate::Migrator;
use tokio::signal::unix::{SignalKind, signal};
use tokio_util::sync::CancellationToken;
use tracing::info;
use tracing_subscriber::EnvFilter;

// Bindet die Fachbereiche ein, damit ihre Operationen (Registrierung über
// `inventory` in `chronos-core`) gelinkt werden, obwohl `chronos-web` sie
// nicht kennt.
use chronos_domain as _;

// Platzhalter, bis das Zusammenstecken die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_channels as _;
use chronos_core as _;
use chronos_web as _;

/// Alle Migrationen, eingebettet aus `crates/chronos/migrations/` (ADR-011).
static MIGRATOR: Migrator = sqlx::migrate!();

/// `EX_UNAVAILABLE` aus `sysexits.h`; nicht 2, das clap für Bedienfehler nutzt.
const EXIT_NOT_IMPLEMENTED: u8 = 69;
/// `EX_TEMPFAIL`: die Schemaversion passte nicht innerhalb der Wartezeit.
const EXIT_SCHEMA_NOT_READY: u8 = 75;
const EXIT_FAILURE: u8 = 1;

/// Migrationsbenutzer (DDL-Rechte), nur für `migrate`.
const ENV_MIGRATE_URL: &str = "DATABASE_URL";
/// Anwendungsbenutzer ohne DDL-Rechte, für `serve` und `worker`.
const ENV_APP_URL: &str = "DATABASE_URL_APP";
const ENV_SCHEMA_WAIT_SECS: &str = "CHRONOS_SCHEMA_WAIT_SECS";
const ENV_WORKER_POLL_MS: &str = "CHRONOS_WORKER_POLL_MS";
const ENV_WORKER_BATCH_SIZE: &str = "CHRONOS_WORKER_BATCH_SIZE";
/// Nur für lokale Entwicklung: `serve` und `worker` migrieren vor dem Start selbst.
const ENV_MIGRATE_ON_START: &str = "CHRONOS_MIGRATE_ON_START";

/// Chronos: Termine und Veranstaltungen für ehrenamtliche Leitungsteams.
#[derive(Debug, Parser)]
#[command(name = "chronos", version)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Startet den Web-Prozess (HTTP-Server und Oberfläche).
    Serve,
    /// Startet den Worker-Prozess (Outbox, Zeitauslöser, Benachrichtigung).
    Worker,
    /// Spielt die Datenbankmigrationen ein (Umgebung: DATABASE_URL).
    Migrate,
}

impl Command {
    fn name(&self) -> &'static str {
        match self {
            Command::Serve => "serve",
            Command::Worker => "worker",
            Command::Migrate => "migrate",
        }
    }
}

#[derive(Debug)]
enum Failure {
    Config(String),
    Database(sqlx::Error),
    Migration(sqlx::migrate::MigrateError),
    Schema(SchemaError),
}

impl Failure {
    fn exit_code(&self) -> u8 {
        match self {
            Failure::Schema(SchemaError::Outdated { .. }) => EXIT_SCHEMA_NOT_READY,
            _ => EXIT_FAILURE,
        }
    }
}

impl std::fmt::Display for Failure {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Failure::Config(message) => f.write_str(message),
            Failure::Database(error) => write!(f, "database error: {error}"),
            Failure::Migration(error) => write!(f, "migration failed: {error}"),
            Failure::Schema(error) => error.fmt(f),
        }
    }
}

fn required_env(name: &str) -> Result<String, Failure> {
    std::env::var(name)
        .map_err(|_| Failure::Config(format!("environment variable {name} is missing")))
}

fn schema_wait() -> Result<Duration, Failure> {
    match std::env::var(ENV_SCHEMA_WAIT_SECS) {
        Err(_) => Ok(db::DEFAULT_SCHEMA_WAIT),
        Ok(value) => value.parse().map(Duration::from_secs).map_err(|_| {
            Failure::Config(format!(
                "{ENV_SCHEMA_WAIT_SECS} must be a whole number of seconds"
            ))
        }),
    }
}

async fn migrate() -> Result<(), Failure> {
    let pool = db::connect(&required_env(ENV_MIGRATE_URL)?)
        .await
        .map_err(Failure::Database)?;
    MIGRATOR.run(&pool).await.map_err(Failure::Migration)?;
    eprintln!(
        "chronos migrate: schema at version {}",
        db::required_version(&MIGRATOR)
    );
    Ok(())
}

/// Gemeinsamer Start von Web und Worker: Schemaversion prüfen, nie selbst migrieren
/// (außer lokal per Schalter).
async fn ensure_schema() -> Result<PgPool, Failure> {
    let wait = schema_wait()?;
    if std::env::var_os(ENV_MIGRATE_ON_START).is_some() {
        migrate().await?;
    }
    let pool = db::connect_lazy(&required_env(ENV_APP_URL)?).map_err(Failure::Database)?;
    db::wait_for_schema(&pool, &MIGRATOR, wait)
        .await
        .map_err(Failure::Schema)?;
    Ok(pool)
}

fn worker_config(poll_ms: Option<&str>, batch_size: Option<&str>) -> Result<WorkerConfig, Failure> {
    let mut config = WorkerConfig::default();
    if let Some(value) = poll_ms {
        config.poll_interval = value.parse().map(Duration::from_millis).map_err(|_| {
            Failure::Config(format!(
                "{ENV_WORKER_POLL_MS} must be a whole number of milliseconds"
            ))
        })?;
    }
    if let Some(value) = batch_size {
        config.batch_size = value.parse::<NonZeroU32>().map_err(|_| {
            Failure::Config(format!(
                "{ENV_WORKER_BATCH_SIZE} must be a whole number greater than zero"
            ))
        })?;
    }
    Ok(config)
}

/// Strukturiertes Log (JSON, eine Zeile je Eintrag) auf stderr; Stufe über `RUST_LOG`.
fn init_logging() {
    tracing_subscriber::fmt()
        .json()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .with_writer(std::io::stderr)
        .init();
}

/// Löst bei SIGTERM (Kubernetes) oder SIGINT (Strg+C) aus.
fn shutdown_on_signal() -> Result<CancellationToken, Failure> {
    let mut terminate = signal(SignalKind::terminate())
        .map_err(|error| Failure::Config(format!("cannot listen for SIGTERM: {error}")))?;
    let token = CancellationToken::new();
    let on_signal = token.clone();
    tokio::spawn(async move {
        tokio::select! {
            _ = terminate.recv() => {}
            _ = tokio::signal::ctrl_c() => {}
        }
        info!("shutdown signal received");
        on_signal.cancel();
    });
    Ok(token)
}

async fn worker() -> Result<(), Failure> {
    init_logging();
    let config = worker_config(
        std::env::var(ENV_WORKER_POLL_MS).ok().as_deref(),
        std::env::var(ENV_WORKER_BATCH_SIZE).ok().as_deref(),
    )?;
    let pool = ensure_schema().await?;
    let shutdown = shutdown_on_signal()?;
    // Noch keine Fachbereiche mit Ereignissen: Alles gilt als „ohne Verbraucher“.
    chronos_worker::run(
        &Outbox::new(pool),
        &ConsumerRegistry::new(),
        &config,
        shutdown,
    )
    .await;
    Ok(())
}

async fn run(command: &Command) -> Result<u8, Failure> {
    match command {
        Command::Migrate => migrate().await.map(|()| 0),
        Command::Worker => worker().await.map(|()| 0),
        Command::Serve => {
            ensure_schema().await?;
            eprintln!("chronos {}: not implemented yet", command.name());
            Ok(EXIT_NOT_IMPLEMENTED)
        }
    }
}

#[tokio::main]
async fn main() -> ExitCode {
    let cli = Cli::parse();
    match run(&cli.command).await {
        Ok(code) => ExitCode::from(code),
        Err(failure) => {
            eprintln!("chronos {}: {failure}", cli.command.name());
            ExitCode::from(failure.exit_code())
        }
    }
}

#[cfg(test)]
mod tests {
    use std::num::NonZeroU32;
    use std::time::Duration;

    use clap::CommandFactory;

    use super::{Cli, worker_config};

    #[test]
    fn cli_definition_is_consistent() {
        Cli::command().debug_assert();
    }

    #[test]
    fn worker_config_defaults_to_two_seconds_and_fifty_events() {
        let config = worker_config(None, None).unwrap();
        assert_eq!(config.poll_interval, Duration::from_secs(2));
        assert_eq!(config.batch_size, NonZeroU32::new(50).unwrap());
    }

    #[test]
    fn worker_config_reads_both_values() {
        let config = worker_config(Some("250"), Some("7")).unwrap();
        assert_eq!(config.poll_interval, Duration::from_millis(250));
        assert_eq!(config.batch_size, NonZeroU32::new(7).unwrap());
    }

    #[test]
    fn worker_config_rejects_invalid_values() {
        assert!(worker_config(Some("soon"), None).is_err());
        assert!(worker_config(None, Some("0")).is_err());
        assert!(worker_config(None, Some("-1")).is_err());
    }
}
