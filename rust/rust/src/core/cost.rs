use serde_json::Value;
use sqlx::PgConnection;
use uuid::Uuid;

/// Kostenposten des Verursachers (V-1 §5): Auslöser ist stets eine Operation mit Korrelations-ID.
pub async fn record(
    conn: &mut PgConnection,
    person_id: &str,
    provider: &str,
    operation: &str,
    correlation_id: &str,
    quantity: Value,
    amount_micro_eur: i64,
) -> Result<(), sqlx::Error> {
    sqlx::query(
        "INSERT INTO cost_entries (id, person_id, provider, trigger_kind, trigger_name, correlation_id, quantity, amount_micro_eur)
         VALUES ($1,$2,$3,'operation',$4,$5,$6,$7)",
    )
    .bind(Uuid::new_v4())
    .bind(person_id)
    .bind(provider)
    .bind(operation)
    .bind(correlation_id)
    .bind(quantity)
    .bind(amount_micro_eur)
    .execute(conn)
    .await?;
    Ok(())
}
