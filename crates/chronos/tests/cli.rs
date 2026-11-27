//! Prüft das Verhalten des Binaries von außen: Hilfe, Version, der Worker und die noch
//! nicht implementierten Unterbefehle. Die Tests mit Datenbank brauchen
//! `DATABASE_URL` und `DATABASE_URL_APP` (`docker compose up --wait`).

use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Output, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use sqlx::{PgPool, postgres::PgPoolOptions};

const EXIT_NOT_IMPLEMENTED: i32 = 69;

const EXIT_USAGE_ERROR: i32 = 2;

fn chronos(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_chronos"))
        .args(args)
        .output()
        .expect("the chronos binary starts")
}

/// `serve` und `worker` prüfen zuerst die Schemaversion; ohne migrierte Datenbank
/// (`DATABASE_URL_APP`) enden sie mit 75, nicht mit 69.
fn chronos_with_env(args: &[&str], env: &[(&str, &str)]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_chronos"))
        .args(args)
        .envs(env.iter().copied())
        .output()
        .expect("the chronos binary starts")
}

#[test]
fn help_lists_all_subcommands() {
    let output = chronos(&["--help"]);
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    for subcommand in ["serve", "worker", "migrate"] {
        assert!(
            stdout.contains(subcommand),
            "--help does not list `{subcommand}`:\n{stdout}"
        );
    }
}

#[test]
fn version_prints_package_version() {
    let output = chronos(&["--version"]);
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert_eq!(
        stdout.trim(),
        format!("chronos {}", env!("CARGO_PKG_VERSION"))
    );
}

#[test]
fn serve_is_not_implemented_yet() {
    let url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP is set for the test");
    let migrate_url = std::env::var("DATABASE_URL").expect("DATABASE_URL is set for the test");
    // Migriert die gemeinsame Datenbank; `migrate` ist idempotent.
    let migrated = chronos_with_env(&["migrate"], &[("DATABASE_URL", &migrate_url)]);
    assert!(migrated.status.success());
    let output = chronos_with_env(&["serve"], &[("DATABASE_URL_APP", &url)]);
    assert_eq!(
        output.status.code(),
        Some(EXIT_NOT_IMPLEMENTED),
        "`chronos serve` should exit with code {EXIT_NOT_IMPLEMENTED} (EX_UNAVAILABLE)"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("not implemented yet"),
        "`chronos serve` printed something unexpected on stderr: {stderr}"
    );
}

const WAIT_LIMIT: Duration = Duration::from_secs(20);

/// Ein laufender `chronos worker` gegen die gemeinsame, migrierte Datenbank.
struct Worker {
    child: Child,
    stderr: Arc<Mutex<Vec<String>>>,
    reader: Option<thread::JoinHandle<()>>,
}

/// Ein fehlgeschlagener Test darf keinen Worker zurücklassen, der weiter die gemeinsame
/// Datenbank abarbeitet.
impl Drop for Worker {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

impl Worker {
    fn start() -> Self {
        let url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP is set for the test");
        let migrate_url = std::env::var("DATABASE_URL").expect("DATABASE_URL is set for the test");
        let migrated = chronos_with_env(&["migrate"], &[("DATABASE_URL", &migrate_url)]);
        assert!(migrated.status.success());

        let mut child = Command::new(env!("CARGO_BIN_EXE_chronos"))
            .arg("worker")
            .env("DATABASE_URL_APP", url)
            .env("CHRONOS_WORKER_POLL_MS", "50")
            .env("CHRONOS_WORKER_LOG_EVENTS", "cli.test")
            .stderr(Stdio::piped())
            .spawn()
            .expect("the chronos binary starts");
        let stderr = Arc::new(Mutex::new(Vec::new()));
        let reader = BufReader::new(child.stderr.take().unwrap());
        let sink = Arc::clone(&stderr);
        let reader = thread::spawn(move || {
            for line in reader.lines().map_while(Result::ok) {
                sink.lock().unwrap().push(line);
            }
        });
        let worker = Self {
            child,
            stderr,
            reader: Some(reader),
        };
        worker.wait_for_log("worker started");
        worker
    }

    fn log(&self) -> String {
        self.stderr.lock().unwrap().join("\n")
    }

    fn wait_for_log(&self, needle: &str) {
        let started = Instant::now();
        while !self.log().contains(needle) {
            assert!(
                started.elapsed() < WAIT_LIMIT,
                "`{needle}` did not show up in the worker log:\n{}",
                self.log()
            );
            thread::sleep(Duration::from_millis(20));
        }
    }

    /// Sendet SIGTERM wie Kubernetes und wartet auf das Ende des Prozesses.
    fn terminate(mut self) -> (std::process::ExitStatus, String) {
        let sent = Command::new("kill")
            .args(["-TERM", &self.child.id().to_string()])
            .status()
            .expect("kill runs");
        assert!(sent.success());
        let started = Instant::now();
        let status = loop {
            if let Some(status) = self.child.try_wait().unwrap() {
                break status;
            }
            if started.elapsed() > WAIT_LIMIT {
                self.child.kill().unwrap();
                panic!("the worker ignored SIGTERM:\n{}", self.log());
            }
            thread::sleep(Duration::from_millis(20));
        };
        self.reader.take().unwrap().join().unwrap();
        let log = self.log();
        (status, log)
    }
}

async fn shared_pool() -> PgPool {
    let url = std::env::var("DATABASE_URL").expect("DATABASE_URL is set for the test");
    PgPoolOptions::new().connect(&url).await.unwrap()
}

/// Ein einziger Test, weil alle Worker dieselbe Datenbank abarbeiten: Ein zweiter Worker
/// könnte das Ereignis sonst vor dem ersten verarbeiten.
#[tokio::test]
async fn worker_process_handles_an_event_with_the_app_role_and_exits_cleanly_on_sigterm() {
    let pool = shared_pool().await;
    let worker = Worker::start();
    let actor: uuid::Uuid =
        sqlx::query_scalar("INSERT INTO person (kind) VALUES ('person') RETURNING id")
            .fetch_one(&pool)
            .await
            .unwrap();
    let correlation_id = uuid::Uuid::new_v4();
    let id: i64 = sqlx::query_scalar(
        "INSERT INTO outbox (event, payload, actor, correlation_id) \
         VALUES ('cli.test', '{}', $1, $2) RETURNING id",
    )
    .bind(actor)
    .bind(correlation_id)
    .fetch_one(&pool)
    .await
    .unwrap();

    let started = Instant::now();
    loop {
        let processed: bool =
            sqlx::query_scalar("SELECT processed_at IS NOT NULL FROM outbox WHERE id = $1")
                .bind(id)
                .fetch_one(&pool)
                .await
                .unwrap();
        if processed {
            break;
        }
        assert!(
            started.elapsed() < WAIT_LIMIT,
            "the worker did not process the event:\n{}",
            worker.log()
        );
        tokio::time::sleep(Duration::from_millis(50)).await;
    }

    let (status, log) = tokio::task::spawn_blocking(move || worker.terminate())
        .await
        .unwrap();
    assert_eq!(status.code(), Some(0), "log:\n{log}");
    assert!(log.contains("shutdown signal received"), "log:\n{log}");
    assert!(log.contains("worker stopped"), "log:\n{log}");
    assert!(
        log.lines()
            .any(|line| line.contains("outbox event received")
                && line.contains(&correlation_id.to_string())),
        "log:\n{log}"
    );
}

#[test]
fn serve_without_database_url_fails_with_config_error() {
    let output = Command::new(env!("CARGO_BIN_EXE_chronos"))
        .arg("serve")
        .env_remove("DATABASE_URL_APP")
        .output()
        .expect("the chronos binary starts");
    assert_eq!(output.status.code(), Some(1));
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("DATABASE_URL_APP"), "stderr: {stderr}");
}

#[test]
fn usage_errors_are_distinguishable_from_not_implemented() {
    for args in [&["unbekannt"][..], &[][..], &["serve", "--unbekannt"][..]] {
        let output = chronos(args);
        assert_eq!(
            output.status.code(),
            Some(EXIT_USAGE_ERROR),
            "`chronos {}` is a usage error and should exit with code {EXIT_USAGE_ERROR}",
            args.join(" ")
        );
    }
}
