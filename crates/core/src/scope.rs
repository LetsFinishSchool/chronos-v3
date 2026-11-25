//! Geltungsbereich: Auf wessen Daten eine Operation wirkt, abgeleitet aus ihren Parametern
//! (ADR-005 Punkt 2, K-002).

use crate::actor::{ActorKind, PersonId, Principal};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Scope {
    /// Jeder Akteur, auch Gäste.
    Public,
    /// Jede angemeldete Person, keine Gäste.
    Authenticated,
    /// Nur dieser Akteur selbst.
    Person(PersonId),
}

impl Scope {
    pub(crate) fn permits(self, principal: &Principal) -> bool {
        match self {
            Self::Public => true,
            Self::Authenticated => principal.kind() == ActorKind::Person,
            Self::Person(id) => principal.id() == id,
        }
    }
}
