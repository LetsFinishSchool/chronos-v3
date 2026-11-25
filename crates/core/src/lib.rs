//! Operationsschicht und gemeinsamer Rahmen (Transaktion, Berechtigung, Verlauf, Outbox).
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

mod actor;
pub mod db;
mod environment;
mod error;
pub mod schema;
mod scope;

pub use actor::{ActorKind, PersonId, Principal};
pub use environment::{Environment, UnknownEnvironment};
pub use error::{Error, ErrorCode};
pub use scope::Scope;
