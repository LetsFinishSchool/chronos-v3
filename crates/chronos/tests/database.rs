//! Datenbanktests gegen echtes PostgreSQL (ADR-009, ADR-011). `#[sqlx::test]` legt je Test
//! eine frische Datenbank an und spielt dieselben Migrationen ein wie `chronos migrate`.
//! Voraussetzung: `docker compose up --wait`, `DATABASE_URL` und `DATABASE_URL_APP`.

use std::time::Duration;

use chronos_core::db::{self, SchemaError};
use sqlx::migrate::Migrator;
use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
use sqlx::{Executor, PgPool};

static MIGRATOR: Migrator = sqlx::migrate!();

const INSUFFICIENT_PRIVILEGE: &str = "42501";

/// Verbindung des Anwendungsbenutzers zur Testdatenbank des Migrationsbenutzers.
async fn app_pool_for(migrate_pool: &PgPool) -> PgPool {
    let app_url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP gesetzt");
    let database = migrate_pool
        .connect_options()
        .get_database()
        .unwrap()
        .to_owned();
    let options: PgConnectOptions = app_url.parse().expect("DATABASE_URL_APP ist gültig");
    PgPoolOptions::new()
        .max_connections(2)
        .connect_with(options.database(&database))
        .await
        .expect("Anwendungsbenutzer verbindet sich")
}

/// Ersetzt den Datenbanknamen in `postgres://benutzer:passwort@host/name?optionen`.
fn with_database(url: &str, database: &str) -> String {
    let (location, query) = url.split_once('?').map_or((url, ""), |(l, q)| (l, q));
    let (prefix, _) = location
        .rsplit_once('/')
        .expect("URL enthält einen Datenbanknamen");
    if query.is_empty() {
        format!("{prefix}/{database}")
    } else {
        format!("{prefix}/{database}?{query}")
    }
}

#[sqlx::test]
async fn sqlx_test_runs_against_postgres(pool: PgPool) {
    let one: i32 = sqlx::query_scalar("SELECT 1")
        .fetch_one(&pool)
        .await
        .unwrap();
    assert_eq!(one, 1);
}

#[sqlx::test(migrations = false)]
async fn migrate_is_idempotent(pool: PgPool) {
    MIGRATOR.run(&pool).await.unwrap();
    MIGRATOR.run(&pool).await.unwrap();
    let applied = db::applied_version(&pool).await.unwrap();
    assert_eq!(applied, Some(db::required_version(&MIGRATOR)));
}

#[sqlx::test(migrations = false)]
async fn schema_check_times_out_on_empty_database(pool: PgPool) {
    let error = db::wait_for_schema(&pool, &MIGRATOR, Duration::ZERO)
        .await
        .expect_err("leere Datenbank ist veraltet");
    assert!(
        matches!(error, SchemaError::Outdated { applied: None, .. }),
        "{error}"
    );
}

#[sqlx::test]
async fn schema_check_passes_on_migrated_database(pool: PgPool) {
    db::wait_for_schema(&pool, &MIGRATOR, Duration::ZERO)
        .await
        .unwrap();
}

#[sqlx::test]
async fn schema_check_allows_database_ahead_of_binary(pool: PgPool) {
    let older = Migrator::with_migrations(Vec::new());
    assert_eq!(db::required_version(&older), 0);
    db::wait_for_schema(&pool, &older, Duration::ZERO)
        .await
        .unwrap();
}

#[sqlx::test]
async fn app_user_can_read_schema_version(pool: PgPool) {
    let app = app_pool_for(&pool).await;
    let applied = db::applied_version(&app).await.unwrap();
    assert_eq!(applied, Some(db::required_version(&MIGRATOR)));
}

#[sqlx::test]
async fn app_user_cannot_run_ddl(pool: PgPool) {
    let app = app_pool_for(&pool).await;
    let error = app
        .execute("CREATE TABLE app_darf_das_nicht (id int)")
        .await
        .expect_err("DDL als Anwendungsbenutzer scheitert");
    let code = error.as_database_error().and_then(|e| e.code());
    assert_eq!(code.as_deref(), Some(INSUFFICIENT_PRIVILEGE), "{error}");
}

#[sqlx::test]
async fn app_user_gets_dml_on_tables_of_later_migrations(pool: PgPool) {
    pool.execute("CREATE TABLE spaeter (id serial PRIMARY KEY, name text)")
        .await
        .unwrap();
    let app = app_pool_for(&pool).await;
    sqlx::query("INSERT INTO spaeter (name) VALUES ('x')")
        .execute(&app)
        .await
        .unwrap();
    let count: i64 = sqlx::query_scalar("SELECT count(*) FROM spaeter")
        .fetch_one(&app)
        .await
        .unwrap();
    assert_eq!(count, 1);
}

#[sqlx::test(migrations = false)]
async fn serve_exits_with_75_when_schema_is_outdated(pool: PgPool) {
    let database = pool.connect_options().get_database().unwrap().to_owned();
    let app_url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP gesetzt");
    let url = with_database(&app_url, &database);
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_chronos"))
        .arg("serve")
        .env("DATABASE_URL_APP", url)
        .env("CHRONOS_SCHEMA_WAIT_SECS", "1")
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(75));
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("chronos migrate"), "{stderr}");
}
