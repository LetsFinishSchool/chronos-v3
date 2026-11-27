//! Der Rahmen führt jede Operation aus und trägt den Querschnitt: Transaktion,
//! Geltungsbereich, Verlauf, Outbox und Probelauf (ADR-005, V2). Er ist der einzige Weg,
//! einen [`Context`] mit Datenbankzugriff zu bekommen.

use serde::Serialize;
use serde_json::{Value, json};
use sqlx::PgPool;
use uuid::Uuid;

use crate::actor::{PersonId, Principal};
use crate::context::{Change, Context, Event};
use crate::environment::Environment;
use crate::error::{Error, ErrorCode};
use crate::operation::{Mode, Registration, all};

/// Feste Kennung des Test-Principals.
const TEST_PRINCIPAL_ID: Uuid = Uuid::from_u128(1);

/// Wirkt der Aufruf, oder läuft er nur zur Vorschau?
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Run {
    Apply,
    /// Probelauf: die Operation läuft vollständig, der Rahmen rollt zurück.
    DryRun,
}

/// Ergebnis eines Aufrufs. Bei einem Probelauf sind `changes` und `events` die Vorschau.
#[derive(Debug, Serialize)]
pub struct Outcome {
    pub result: Value,
    pub changes: Vec<Change>,
    pub events: Vec<Event>,
    pub applied: bool,
}

#[derive(Clone)]
pub struct Frame {
    pool: PgPool,
    environment: Environment,
}

impl Frame {
    pub const fn new(pool: PgPool, environment: Environment) -> Self {
        Self { pool, environment }
    }

    /// Principal für Entwicklung und Tests. In Produktion nicht verfügbar.
    pub async fn test_principal(&self) -> Result<Principal, Error> {
        if !self.environment.allows_test_principal() {
            return Err(Error::new(ErrorCode::TestPrincipalForbidden));
        }
        let principal = Principal::person(PersonId::new(TEST_PRINCIPAL_ID));
        sqlx::query("INSERT INTO person (id, kind) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING")
            .bind(TEST_PRINCIPAL_ID)
            .bind(principal.kind().as_db())
            .execute(&self.pool)
            .await?;
        Ok(principal)
    }

    pub async fn execute(
        &self,
        principal: &Principal,
        name: &str,
        params: Value,
        correlation_id: Uuid,
        run: Run,
    ) -> Result<Outcome, Error> {
        let registration = Registration::find(name)
            .ok_or_else(|| Error::new(ErrorCode::UnknownOperation).with("operation", name))?;

        // Vor jedem Datenbankzugriff: Die Ablehnung sieht für fremde und fehlende Objekte
        // gleich aus (`ErrorCode::NotFound`).
        if !(registration.scope)(&params)?.permits(principal) {
            return Err(Error::not_found());
        }

        let mut transaction = self.pool.begin().await?;
        if registration.mode == Mode::Read {
            sqlx::query("SET TRANSACTION READ ONLY")
                .execute(&mut *transaction)
                .await?;
        }

        let mut context = Context::new(&mut transaction, *principal, registration.mode);
        let result = (registration.run)(&mut context, params).await?;
        let (changes, events) = context.into_parts();

        if run == Run::DryRun {
            transaction.rollback().await?;
            return Ok(Outcome {
                result,
                changes,
                events,
                applied: false,
            });
        }

        for change in &changes {
            sqlx::query(
                "INSERT INTO history (actor_id, action, object_kind, object_id, before, correlation_id) \
                 VALUES ($1, $2, $3, $4, $5, $6)",
            )
            .bind(principal.id().uuid())
            .bind(&change.action)
            .bind(&change.object_kind)
            .bind(change.object_id)
            .bind(&change.before)
            .bind(correlation_id)
            .execute(&mut *transaction)
            .await?;
        }
        for event in &events {
            sqlx::query(
                "INSERT INTO outbox (event, payload, actor_id, correlation_id) \
                 VALUES ($1, $2, $3, $4)",
            )
            .bind(&event.name)
            .bind(&event.payload)
            .bind(principal.id().uuid())
            .bind(correlation_id)
            .execute(&mut *transaction)
            .await?;
        }
        transaction.commit().await?;

        Ok(Outcome {
            result,
            changes,
            events,
            applied: true,
        })
    }

    /// Operationsliste mit Schemas, nach Name sortiert. Grundlage für Oberfläche,
    /// Assistent und den Snapshot-Test.
    pub fn describe() -> Value {
        let mut registrations: Vec<_> = all().collect();
        registrations.sort_by_key(|registration| registration.name);
        Value::Array(
            registrations
                .into_iter()
                .map(|registration| {
                    json!({
                        "name": registration.name,
                        "description": registration.description,
                        "mode": registration.mode,
                        "params": (registration.params_schema)(),
                        "result": (registration.result_schema)(),
                    })
                })
                .collect(),
        )
    }
}
