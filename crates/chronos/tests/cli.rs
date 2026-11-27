//! Prüft das Verhalten des Binaries von außen: Hilfe, Version und die noch
//! nicht implementierten Unterbefehle. Die Tests mit Datenbank brauchen
//! `DATABASE_URL` und `DATABASE_URL_APP` (`docker compose up --wait`).

use std::process::{Command, Output};

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
fn serve_and_worker_are_not_implemented_yet() {
    let url = std::env::var("DATABASE_URL_APP").expect("DATABASE_URL_APP is set for the test");
    let migrate_url = std::env::var("DATABASE_URL").expect("DATABASE_URL is set for the test");
    // Migriert die gemeinsame Datenbank; `migrate` ist idempotent.
    let migrated = chronos_with_env(&["migrate"], &[("DATABASE_URL", &migrate_url)]);
    assert!(migrated.status.success());
    for subcommand in ["serve", "worker"] {
        let output = chronos_with_env(&[subcommand], &[("DATABASE_URL_APP", &url)]);
        assert_eq!(
            output.status.code(),
            Some(EXIT_NOT_IMPLEMENTED),
            "`chronos {subcommand}` should exit with code {EXIT_NOT_IMPLEMENTED} (EX_UNAVAILABLE)"
        );
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(
            stderr.contains("not implemented yet"),
            "`chronos {subcommand}` printed something unexpected on stderr: {stderr}"
        );
    }
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
