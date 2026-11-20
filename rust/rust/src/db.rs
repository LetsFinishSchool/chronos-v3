use sqlx::postgres::{PgPool, PgPoolOptions};
use std::time::{Duration, Instant};

pub async fn connect(url: &str) -> Result<PgPool, sqlx::Error> {
    let start = Instant::now();
    loop {
        match PgPoolOptions::new().max_connections(20).acquire_timeout(Duration::from_secs(10)).connect(url).await {
            Ok(p) => return Ok(p),
            Err(e) if start.elapsed() < Duration::from_secs(60) => {
                tracing::warn!(error = %e, "Datenbank noch nicht erreichbar");
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
            Err(e) => return Err(e),
        }
    }
}

pub async fn migrate(pool: &PgPool) -> Result<(), sqlx::migrate::MigrateError> {
    sqlx::migrate!("./migrations").run(pool).await
}

/// Der Worker wartet bis zu `max` auf das Schema (das Web führt die Migrationen aus).
pub async fn wait_for_schema(pool: &PgPool, max: Duration) -> crate::error::BoxResult {
    let start = Instant::now();
    loop {
        if sqlx::query("SELECT 1 FROM delivery_tasks LIMIT 1").execute(pool).await.is_ok() {
            return Ok(());
        }
        if start.elapsed() > max {
            return Err("Schema nach 60 s nicht vorhanden".into());
        }
        tokio::time::sleep(Duration::from_millis(500)).await;
    }
}
