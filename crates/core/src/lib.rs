//! Operationsschicht und gemeinsamer Rahmen (Transaktion, Berechtigung, Verlauf, Outbox).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

mod actor;
mod consumer;
mod context;
pub mod db;
mod environment;
mod error;
mod frame;
mod operation;
mod outbox;
pub mod schema;
mod scope;

pub use actor::{ActorKind, PersonId, Principal};
pub use consumer::{Consumer, ConsumerError, ConsumerFuture, ConsumerRegistry, OutboxEvent};
pub use context::{Change, Context, Event};
pub use environment::{Environment, UnknownEnvironment};
pub use error::{Error, ErrorCode};
pub use frame::{Frame, Outcome, Run};
#[doc(hidden)]
pub use inventory;
pub use operation::{Mode, Operation, Registration, all as registered_operations};
pub use outbox::{BatchStats, Outbox, OutboxError};
pub use scope::Scope;
