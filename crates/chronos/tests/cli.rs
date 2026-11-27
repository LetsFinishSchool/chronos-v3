//! Prüft das Verhalten des Binaries von außen: Hilfe, Version, `serve` und der
//! noch nicht implementierte Unterbefehl `worker`. Die Tests mit Datenbank brauchen
//! `DATABASE_URL` und `DATABASE_URL_APP` (`docker compose up --wait`).

use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::process::{Command, Output, Stdio};

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
fn worker_is_not_implemented_yet() {
    let url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP is set for the test");
    let migrate_url = std::env::var("DATABASE_URL").expect("DATABASE_URL is set for the test");
    // Migriert die gemeinsame Datenbank; `migrate` ist idempotent.
    let migrated = chronos_with_env(&["migrate"], &[("DATABASE_URL", &migrate_url)]);
    assert!(migrated.status.success());
    let output = chronos_with_env(&["worker"], &[("DATABASE_URL_APP", &url)]);
    assert_eq!(
        output.status.code(),
        Some(EXIT_NOT_IMPLEMENTED),
        "`chronos worker` should exit with code {EXIT_NOT_IMPLEMENTED} (EX_UNAVAILABLE)"
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("not implemented yet"),
        "`chronos worker` printed something unexpected on stderr: {stderr}"
    );
}

#[test]
fn serve_with_invalid_listen_address_fails_with_config_error() {
    let output = Command::new(env!("CARGO_BIN_EXE_chronos"))
        .arg("serve")
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
