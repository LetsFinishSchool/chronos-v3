//! Operationsschicht und gemeinsamer Rahmen (Transaktion, Berechtigung, Verlauf, Outbox).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

mod actor;
mod context;
pub mod db;
mod environment;
mod error;
mod frame;
mod operation;
pub mod schema;
mod scope;

pub use actor::{ActorKind, PersonId, Principal};
pub use context::{Change, Context, Event};
pub use environment::{Environment, UnknownEnvironment};
pub use error::{Error, ErrorCode};
pub use frame::{Frame, Outcome, Run};
#[doc(hidden)]
pub use inventory;
pub use operation::{Mode, Operation, Registration, all as registered_operations};
pub use scope::Scope;
