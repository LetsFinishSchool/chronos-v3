//! Checks the binary's behaviour from the outside: help, version, `serve` and the worker.
//! The tests with a database need `DATABASE_URL` and `DATABASE_URL_APP`
//! (`docker compose up --wait`).

use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::process::{Child, Command, Output, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use sqlx::{PgPool, postgres::PgPoolOptions};

const EXIT_USAGE_ERROR: i32 = 2;
/// Minimal build directory for `serve`, which refuses to start without a frontend.
const FRONTEND_FIXTURE: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/frontend");

fn chronos(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_chronos"))
        .args(args)
        .output()
        .expect("the chronos binary starts")
}

/// Runs the binary with extra environment variables, e.g. `DATABASE_URL` for `migrate`.
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
fn serve_with_invalid_listen_address_fails_with_config_error() {
    let output = Command::new(env!("CARGO_BIN_EXE_chronos"))
        .arg("serve")
        .env("CHRONOS_FRONTEND_DIR", FRONTEND_FIXTURE)
        .env("CHRONOS_LISTEN", "not-an-address")
        .env_remove("DATABASE_URL_APP")
        .output()
        .expect("the chronos binary starts");
    assert_eq!(output.status.code(), Some(1));
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("CHRONOS_LISTEN"), "stderr: {stderr}");
}

#[test]
fn serve_answers_healthz_and_exits_cleanly_on_sigterm() {
    let url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP is set for the test");
    let migrate_url = std::env::var("DATABASE_URL").expect("DATABASE_URL is set for the test");
    let migrated = chronos_with_env(&["migrate"], &[("DATABASE_URL", &migrate_url)]);
    assert!(migrated.status.success());

    let mut child = Command::new(env!("CARGO_BIN_EXE_chronos"))
        .arg("serve")
        .env("DATABASE_URL_APP", &url)
        .env("CHRONOS_FRONTEND_DIR", FRONTEND_FIXTURE)
        .env("CHRONOS_LISTEN", "127.0.0.1:0")
        .stderr(Stdio::piped())
        .spawn()
        .expect("the chronos binary starts");
    let mut stderr = BufReader::new(child.stderr.take().expect("stderr is piped"));
    let mut line = String::new();
    stderr
        .read_line(&mut line)
        .expect("serve reports its address");
    let address = line
        .trim()
        .rsplit(' ')
        .next()
        .expect("the line ends with the address")
        .to_owned();

    let mut stream = TcpStream::connect(&address).expect("serve accepts connections");
    stream
        .write_all(b"GET /healthz HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n")
        .unwrap();
    let mut response = String::new();
    stream.read_to_string(&mut response).unwrap();
    assert!(response.starts_with("HTTP/1.1 200"), "{response}");

    let killed = Command::new("kill")
        .args(["-TERM", &child.id().to_string()])
        .status()
        .expect("kill runs");
    assert!(killed.success());
    assert_eq!(child.wait().unwrap().code(), Some(0));
}

const WAIT_LIMIT: Duration = Duration::from_secs(20);

/// A running `chronos worker` against the shared, migrated database.
struct Worker {
    child: Child,
    stderr: Arc<Mutex<Vec<String>>>,
    reader: Option<thread::JoinHandle<()>>,
}

/// A failed test must not leave a worker behind that keeps processing the shared
/// database.
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

    /// Sends SIGTERM like Kubernetes and waits for the process to end.
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

/// A single test, because all workers process the same database: a second worker could
/// otherwise handle the event before the first.
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
        .env("CHRONOS_FRONTEND_DIR", FRONTEND_FIXTURE)
        .env_remove("DATABASE_URL_APP")
        .output()
        .expect("the chronos binary starts");
    assert_eq!(output.status.code(), Some(1));
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("DATABASE_URL_APP"), "stderr: {stderr}");
}

#[test]
fn serve_with_missing_frontend_dir_fails_with_config_error() {
    let output = Command::new(env!("CARGO_BIN_EXE_chronos"))
        .arg("serve")
        .env("CHRONOS_FRONTEND_DIR", "/nonexistent/chronos-frontend")
        .env_remove("DATABASE_URL_APP")
        .output()
        .expect("the chronos binary starts");
    assert_eq!(output.status.code(), Some(1));
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("CHRONOS_FRONTEND_DIR"), "stderr: {stderr}");
    assert!(
        stderr.contains("npm --prefix frontend run build"),
        "stderr: {stderr}"
    );
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
