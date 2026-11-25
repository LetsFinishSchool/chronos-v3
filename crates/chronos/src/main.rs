//! Einstiegspunkt: ein Binary mit Unterbefehlen für alle Prozesse (ADR-002, ADR-011).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use std::process::ExitCode;

use clap::{Parser, Subcommand};

// Bindet die Fachbereiche ein, damit ihre Operationen (Registrierung über
// `inventory` in `chronos-core`) gelinkt werden, obwohl `chronos-web` sie
// nicht kennt.
use chronos_domain as _;

// Platzhalter, bis das Zusammenstecken die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_channels as _;
use chronos_core as _;
use chronos_web as _;
use chronos_worker as _;
use sqlx as _;
use tokio as _;

/// `EX_UNAVAILABLE` aus `sysexits.h`; nicht 2, das clap für Bedienfehler nutzt.
const EXIT_NOT_IMPLEMENTED: u8 = 69;

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
    /// Führt die Datenbankmigrationen aus.
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

fn main() -> ExitCode {
    let cli = Cli::parse();
    eprintln!("chronos {}: noch nicht implementiert", cli.command.name());
    ExitCode::from(EXIT_NOT_IMPLEMENTED)
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
