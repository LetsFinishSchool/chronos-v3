//! Einstiegspunkt von Chronos: ein Binary mit Unterbefehlen für alle Prozesse.
//!
//! Zuständig für die Unterbefehle `serve`, `worker` und `migrate` (später
//! Import) in einem Image für alle (ADR-002, ADR-011), für das Laden der
//! Konfiguration aus Umgebung und Secrets, das Initialisieren von Logging und
//! Tracing, das Zusammenstecken aller Crates (`chronos-domain` einbinden,
//! Adapter und Kanäle erzeugen und an Web und Worker übergeben) und für die
//! eingebetteten Migrationen von `chronos migrate`.
//!
//! Nicht zuständig für Fachlogik, Berechtigungen und Protokolle: Alles, was
//! ein anderes Crate brauchen könnte, gehört dorthin. Von `chronos` hängt kein
//! anderes Crate ab.
//!
//! Crate-Zuschnitt: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use std::process::ExitCode;

use clap::{Parser, Subcommand};

// Bindet die Fachbereiche ein, damit ihre Operationen (Registrierung über
// `inventory` in `chronos-core`) gelinkt werden, obwohl `chronos-web` sie
// nicht kennt.
use chronos_domain as _;

/// Exit-Code für Unterbefehle, die es noch nicht gibt.
const EXIT_NOT_IMPLEMENTED: u8 = 2;

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
