//! Fehler als Codes mit Parametern; Texte entstehen erst im Client (ADR-005 Punkt 7).

use std::collections::BTreeMap;
use std::fmt;

use serde::Serialize;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ErrorCode {
    /// Objekt fehlt **oder** liegt außerhalb des Geltungsbereichs; beides sieht gleich aus,
    /// damit die Antwort die Existenz nicht verrät.
    NotFound,
    UnknownOperation,
    InvalidParams,
    /// Eine lesende Operation hat zu schreiben versucht.
    ReadOnly,
    TestPrincipalForbidden,
    Database,
}

impl ErrorCode {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::NotFound => "not_found",
            Self::UnknownOperation => "unknown_operation",
            Self::InvalidParams => "invalid_params",
            Self::ReadOnly => "read_only",
            Self::TestPrincipalForbidden => "test_principal_forbidden",
            Self::Database => "database",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Error {
    pub code: ErrorCode,
    pub params: BTreeMap<String, String>,
}

impl Error {
    pub const fn new(code: ErrorCode) -> Self {
        Self {
            code,
            params: BTreeMap::new(),
        }
    }

    #[must_use]
    pub fn with(mut self, key: &str, value: impl Into<String>) -> Self {
        self.params.insert(key.to_owned(), value.into());
        self
    }

    pub const fn not_found() -> Self {
        Self::new(ErrorCode::NotFound)
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.code.as_str())?;
        for (key, value) in &self.params {
            write!(f, " {key}={value}")?;
        }
        Ok(())
    }
}

impl std::error::Error for Error {}

/// SQLSTATE `25006`: Schreibversuch in einer `READ ONLY`-Transaktion.
const READ_ONLY_SQL_TRANSACTION: &str = "25006";

impl From<sqlx::Error> for Error {
    fn from(error: sqlx::Error) -> Self {
        let sqlstate = error
            .as_database_error()
            .and_then(|db| db.code())
            .map(|code| code.into_owned());
        match sqlstate.as_deref() {
            Some(READ_ONLY_SQL_TRANSACTION) => Self::new(ErrorCode::ReadOnly),
            Some(code) => Self::new(ErrorCode::Database).with("sqlstate", code),
            None => Self::new(ErrorCode::Database),
        }
    }
}
