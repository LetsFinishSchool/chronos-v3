//! Operation-Trait und Registrierung über `inventory` (ADR-005 Punkt 1).

use std::future::Future;
use std::pin::Pin;

use serde::Serialize;
use serde::de::DeserializeOwned;
use serde_json::Value;

use crate::context::Context;
use crate::error::{Error, ErrorCode};
use crate::schema::{self, JsonSchema};
use crate::scope::Scope;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    /// Läuft in einer `READ ONLY`-Transaktion; PostgreSQL erzwingt das.
    Read,
    Write,
}

/// Eine Operation besteht nur aus Fachlogik. Transaktion, Berechtigung, Verlauf und Outbox
/// übernimmt der Rahmen. Registrierung: [`register_operation!`].
pub trait Operation: 'static {
    type Params: DeserializeOwned + JsonSchema + Send;
    type Output: Serialize + JsonSchema + Send;

    /// Name nach dem Muster `bereich.verb`.
    const NAME: &'static str;
    /// Beschreibung für Assistent und Operationsliste, auf Englisch (ADR-005).
    const DESCRIPTION: &'static str;
    const MODE: Mode;

    /// Auf wessen Daten die Operation mit diesen Parametern wirkt.
    fn scope(params: &Self::Params) -> Scope;

    fn run(
        ctx: &mut Context<'_>,
        params: Self::Params,
    ) -> impl Future<Output = Result<Self::Output, Error>> + Send;
}

type BoxFuture<'a, T> = Pin<Box<dyn Future<Output = T> + Send + 'a>>;

/// Typlose Fassung einer [`Operation`] für das Verzeichnis. Nur über
/// [`Registration::of`] erzeugbar.
pub struct Registration {
    pub name: &'static str,
    pub description: &'static str,
    pub mode: Mode,
    pub params_schema: fn() -> Value,
    pub result_schema: fn() -> Value,
    pub(crate) scope: fn(&Value) -> Result<Scope, Error>,
    pub(crate) run:
        for<'a, 't> fn(&'a mut Context<'t>, Value) -> BoxFuture<'a, Result<Value, Error>>,
}

inventory::collect!(Registration);

impl Registration {
    pub const fn of<O: Operation>() -> Self {
        Self {
            name: O::NAME,
            description: O::DESCRIPTION,
            mode: O::MODE,
            params_schema: schema::of::<O::Params>,
            result_schema: schema::of::<O::Output>,
            scope: scope_of::<O>,
            run: run_erased::<O>,
        }
    }

    pub fn find(name: &str) -> Option<&'static Self> {
        all().find(|registration| registration.name == name)
    }
}

/// Alle registrierten Operationen in unbestimmter Reihenfolge.
pub fn all() -> impl Iterator<Item = &'static Registration> {
    inventory::iter::<Registration>.into_iter()
}

fn invalid_params(name: &str) -> Error {
    Error::new(ErrorCode::InvalidParams).with("operation", name)
}

fn scope_of<O: Operation>(params: &Value) -> Result<Scope, Error> {
    let params: O::Params =
        serde_json::from_value(params.clone()).map_err(|_| invalid_params(O::NAME))?;
    Ok(O::scope(&params))
}

fn run_erased<'a, 't, O: Operation>(
    ctx: &'a mut Context<'t>,
    params: Value,
) -> BoxFuture<'a, Result<Value, Error>> {
    Box::pin(async move {
        let params: O::Params =
            serde_json::from_value(params).map_err(|_| invalid_params(O::NAME))?;
        let output = O::run(ctx, params).await?;
        serde_json::to_value(output).map_err(|_| Error::new(ErrorCode::Database))
    })
}

/// Trägt eine [`Operation`] ins Verzeichnis ein; keine zweite Liste von Hand.
#[macro_export]
macro_rules! register_operation {
    ($operation:ty) => {
        $crate::inventory::submit!($crate::Registration::of::<$operation>());
    };
}
