//! Worker-Prozess: Outbox, Benachrichtigung, Zeitauslöser.
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

mod consumer;
mod log_consumer;
mod outbox;
mod runner;

pub use consumer::{Consumer, ConsumerError, ConsumerFuture, OutboxEvent, Registry};
pub use log_consumer::LogConsumer;
pub use outbox::{BatchStats, process_batch};
pub use runner::{WorkerConfig, run};

// Platzhalter, bis Code die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_channels as _;
use chronos_core as _;
