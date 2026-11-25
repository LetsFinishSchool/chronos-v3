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

#[cfg(test)]
mod tests {
    use uuid::Uuid;

    use super::*;

    fn id() -> PersonId {
        PersonId::new(Uuid::new_v4())
    }

    #[test]
    fn public_permits_guests() {
        assert!(Scope::Public.permits(&Principal::guest(id())));
    }

    #[test]
    fn authenticated_refuses_guests() {
        assert!(Scope::Authenticated.permits(&Principal::person(id())));
        assert!(!Scope::Authenticated.permits(&Principal::guest(id())));
    }

    #[test]
    fn person_scope_permits_only_that_actor() {
        let owner = id();
        assert!(Scope::Person(owner).permits(&Principal::person(owner)));
        assert!(!Scope::Person(owner).permits(&Principal::person(id())));
    }
}
