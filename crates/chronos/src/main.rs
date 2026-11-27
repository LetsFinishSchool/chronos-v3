//! Einstiegspunkt: ein Binary mit Unterbefehlen für alle Prozesse (ADR-002, ADR-011).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use std::future::Future;
use std::net::SocketAddr;
use std::process::ExitCode;
use std::time::Duration;

use chronos_core::db::{self, SchemaError};
use clap::{Parser, Subcommand};
use sqlx::migrate::Migrator;
use tokio::net::TcpListener;
use tokio::signal::unix::{SignalKind, signal};

// Bindet die Fachbereiche ein, damit ihre Operationen (Registrierung über
// `inventory` in `chronos-core`) gelinkt werden, obwohl `chronos-web` sie
// nicht kennt.
use chronos_domain as _;

// Platzhalter, bis das Zusammenstecken die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_channels as _;
use chronos_core as _;
use chronos_worker as _;

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
/// Nur für lokale Entwicklung: `serve` und `worker` migrieren vor dem Start selbst.
const ENV_MIGRATE_ON_START: &str = "CHRONOS_MIGRATE_ON_START";
const ENV_LISTEN: &str = "CHRONOS_LISTEN";
const DEFAULT_LISTEN: &str = "127.0.0.1:8080";

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
    Io(std::io::Error),
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
            Failure::Io(error) => write!(f, "I/O error: {error}"),
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

fn listen_address() -> Result<SocketAddr, Failure> {
    let value = std::env::var(ENV_LISTEN).unwrap_or_else(|_| DEFAULT_LISTEN.to_owned());
    value.parse().map_err(|_| {
        Failure::Config(format!(
            "{ENV_LISTEN} must be an address like {DEFAULT_LISTEN}, got `{value}`"
        ))
    })
}

/// Completes on SIGTERM (container stop) or Ctrl+C.
fn shutdown_signal() -> Result<impl Future<Output = ()> + Send + 'static, Failure> {
    let mut sigterm = signal(SignalKind::terminate()).map_err(Failure::Io)?;
    let mut sigint = signal(SignalKind::interrupt()).map_err(Failure::Io)?;
    Ok(async move {
        tokio::select! {
            _ = sigterm.recv() => {}
            _ = sigint.recv() => {}
        }
    })
}

async fn serve() -> Result<(), Failure> {
    let address = listen_address()?;
    ensure_schema().await?;
    let listener = TcpListener::bind(address).await.map_err(Failure::Io)?;
    let bound = listener.local_addr().map_err(Failure::Io)?;
    let shutdown = shutdown_signal()?;
    eprintln!("chronos serve: listening on {bound}");
    chronos_web::serve(listener, shutdown)
        .await
        .map_err(Failure::Io)
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
async fn ensure_schema() -> Result<(), Failure> {
    let wait = schema_wait()?;
    if std::env::var_os(ENV_MIGRATE_ON_START).is_some() {
        migrate().await?;
    }
    let pool = db::connect_lazy(&required_env(ENV_APP_URL)?).map_err(Failure::Database)?;
    db::wait_for_schema(&pool, &MIGRATOR, wait)
        .await
        .map_err(Failure::Schema)
}

async fn run(command: &Command) -> Result<u8, Failure> {
    match command {
        Command::Migrate => migrate().await.map(|()| 0),
        Command::Serve => serve().await.map(|()| 0),
        Command::Worker => {
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
    use clap::CommandFactory;

    use super::Cli;

    #[test]
    fn cli_definition_is_consistent() {
        Cli::command().debug_assert();
    }
}
