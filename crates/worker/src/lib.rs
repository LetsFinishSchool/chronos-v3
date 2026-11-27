//! Worker-Prozess: Outbox, Benachrichtigung, Zeitauslöser.
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

mod consumer;
mod outbox;

pub use consumer::{Consumer, ConsumerError, ConsumerFuture, OutboxEvent, Registry};
pub use outbox::{BatchStats, process_batch};

// Platzhalter, bis Code die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_channels as _;
use chronos_core as _;
