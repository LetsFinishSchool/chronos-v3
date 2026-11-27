//! Akteure: Wer eine Operation ausführt (K-004, ADR-005 Punkt 7).

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::JsonSchema;

/// Identifier of a person or guest.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize, JsonSchema)]
#[serde(transparent)]
pub struct PersonId(Uuid);

impl PersonId {
    pub const fn new(id: Uuid) -> Self {
        Self(id)
    }

    pub const fn uuid(self) -> Uuid {
        self.0
    }
}

/// Art des Akteurs. Assistent, Regel und Import kommen mit ihren Features.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActorKind {
    Person,
    Guest,
}

impl ActorKind {
    /// Wert der Spalte `person.kind`.
    pub const fn as_db(self) -> &'static str {
        match self {
            Self::Person => "person",
            Self::Guest => "guest",
        }
    }
}

/// Der angemeldete Akteur. Die Konstruktoren sind nicht öffentlich: Sonst könnte jeder Code
/// beliebige Akteure erzeugen und die Sperre des Test-Principals umgehen. Erzeugen dürfen ihn
/// nur der Rahmen (`Frame::test_principal`, `Frame::test_actor`) und später der Login-Pfad.
///
/// ```compile_fail,E0624
/// let id = chronos_core::PersonId::new(uuid::Uuid::nil());
/// let _ = chronos_core::Principal::person(id);
/// ```
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Principal {
    id: PersonId,
    kind: ActorKind,
}

impl Principal {
    pub(crate) const fn person(id: PersonId) -> Self {
        Self {
            id,
            kind: ActorKind::Person,
        }
    }

    pub(crate) const fn guest(id: PersonId) -> Self {
        Self {
            id,
            kind: ActorKind::Guest,
        }
    }

    pub const fn id(&self) -> PersonId {
        self.id
    }

    pub const fn kind(&self) -> ActorKind {
        self.kind
    }
}
