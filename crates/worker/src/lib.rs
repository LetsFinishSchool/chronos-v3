//! Worker process: outbox, notifications, time triggers.
//!
//! Layout and allowed dependencies: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

mod log_consumer;
mod runner;

pub use log_consumer::LogConsumer;
pub use runner::{WorkerConfig, run};

// Placeholder until code uses the dependencies (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_channels as _;
