//! Der Kontext, den der Rahmen einer Operation übergibt (ADR-005 Punkt 2).

use serde::Serialize;
use serde_json::Value;
use sqlx::PgConnection;
use uuid::Uuid;

use crate::actor::Principal;
use crate::error::{Error, ErrorCode};
use crate::operation::Mode;

/// Eine Änderung an einem Objekt. Der Rahmen schreibt daraus den Verlauf und bildet die
/// Vorschau des Probelaufs.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct Change {
    pub action: String,
    pub object_kind: String,
    pub object_id: Uuid,
    /// Zustand vor der Änderung; `None` bei neuen Objekten.
    pub previous_state: Option<Value>,
    /// Zustand danach; `None` bei gelöschten Objekten. Nur für die Vorschau, der
    /// Verlauf speichert ihn nicht.
    pub new_state: Option<Value>,
}

/// Ein fachliches Ereignis für die Outbox (K-003).
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct Event {
    pub name: String,
    pub payload: Value,
}

/// Einziger Weg zur Datenbank für Fachlogik. Der Konstruktor ist nicht öffentlich: Nur der
/// Rahmen erzeugt einen Kontext, und zwar innerhalb seiner Transaktion.
///
/// ```compile_fail,E0624
/// fn bypass(connection: &mut sqlx::PgConnection, principal: chronos_core::Principal) {
///     let _ = chronos_core::Context::new(connection, principal, chronos_core::Mode::Write);
/// }
/// ```
pub struct Context<'t> {
    connection: &'t mut PgConnection,
    principal: Principal,
    mode: Mode,
    changes: Vec<Change>,
    events: Vec<Event>,
}

impl<'t> Context<'t> {
    pub(crate) fn new(connection: &'t mut PgConnection, principal: Principal, mode: Mode) -> Self {
        Self {
            connection,
            principal,
            mode,
            changes: Vec::new(),
            events: Vec::new(),
        }
    }

    pub const fn principal(&self) -> Principal {
        self.principal
    }

    /// Verbindung innerhalb der Transaktion des Rahmens.
    pub fn db(&mut self) -> &mut PgConnection {
        self.connection
    }

    /// Meldet eine Änderung; der Rahmen schreibt den Verlauf.
    pub fn record_change(&mut self, change: Change) -> Result<(), Error> {
        self.require_write()?;
        self.changes.push(change);
        Ok(())
    }

    /// Meldet ein Ereignis; der Rahmen schreibt es in die Outbox.
    pub fn emit(&mut self, event: Event) -> Result<(), Error> {
        self.require_write()?;
        self.events.push(event);
        Ok(())
    }

    fn require_write(&self) -> Result<(), Error> {
        match self.mode {
            Mode::Write => Ok(()),
            Mode::Read => Err(Error::new(ErrorCode::ReadOnly)),
        }
    }

    pub(crate) fn into_parts(self) -> (Vec<Change>, Vec<Event>) {
        (self.changes, self.events)
    }
}
