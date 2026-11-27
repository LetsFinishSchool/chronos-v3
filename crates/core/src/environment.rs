//! Laufumgebung. Sie entscheidet, ob der Test-Principal existieren darf.

use std::fmt;

const VARIABLE: &str = "CHRONOS_ENV";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Environment {
    Development,
    Test,
    Production,
}

#[derive(Debug, PartialEq, Eq)]
pub struct UnknownEnvironment(pub String);

impl fmt::Display for UnknownEnvironment {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "unknown_environment value={}", self.0)
    }
}

impl std::error::Error for UnknownEnvironment {}

impl Environment {
    /// Nur die drei Namen sind gültig; alles andere ist ein Fehler statt einer
    /// stillen Entwicklungsumgebung.
    pub fn parse(name: &str) -> Result<Self, UnknownEnvironment> {
        match name {
            "development" => Ok(Self::Development),
            "test" => Ok(Self::Test),
            "production" => Ok(Self::Production),
            other => Err(UnknownEnvironment(other.to_owned())),
        }
    }

    /// Liest `CHRONOS_ENV`. Ohne Angabe gilt Produktion, damit ein vergessenes Setzen
    /// nie den Test-Principal freischaltet.
    pub fn from_env() -> Result<Self, UnknownEnvironment> {
        std::env::var(VARIABLE).map_or(Ok(Self::Production), |name| Self::parse(&name))
    }

    pub const fn allows_test_principal(self) -> bool {
        !matches!(self, Self::Production)
    }
}
