//! Prüft das Verhalten des Binaries von außen: Hilfe, Version und die noch
//! nicht implementierten Unterbefehle.

use std::process::{Command, Output};

/// `EX_UNAVAILABLE` aus `sysexits.h`: Unterbefehl gibt es noch nicht.
const EXIT_NOT_IMPLEMENTED: i32 = 69;

/// Exit-Code von clap bei Bedienfehlern.
const EXIT_USAGE_ERROR: i32 = 2;

fn chronos(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_chronos"))
        .args(args)
        .output()
        .expect("Binary chronos lässt sich starten")
}

#[test]
fn help_lists_all_subcommands() {
    let output = chronos(&["--help"]);
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    for subcommand in ["serve", "worker", "migrate"] {
        assert!(
            stdout.contains(subcommand),
            "--help nennt `{subcommand}` nicht:\n{stdout}"
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
fn subcommands_are_not_implemented_yet() {
    for subcommand in ["serve", "worker", "migrate"] {
        let output = chronos(&[subcommand]);
        assert_eq!(
            output.status.code(),
            Some(EXIT_NOT_IMPLEMENTED),
            "`chronos {subcommand}` soll mit Exit-Code {EXIT_NOT_IMPLEMENTED} (EX_UNAVAILABLE) enden"
        );
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(
            stderr.contains("noch nicht implementiert"),
            "`chronos {subcommand}` meldet auf stderr nichts Erwartetes: {stderr}"
        );
    }
}

#[test]
fn usage_errors_are_distinguishable_from_not_implemented() {
    for args in [&["unbekannt"][..], &[][..], &["serve", "--unbekannt"][..]] {
        let output = chronos(args);
        assert_eq!(
            output.status.code(),
            Some(EXIT_USAGE_ERROR),
            "`chronos {}` ist ein Bedienfehler und soll mit Exit-Code {EXIT_USAGE_ERROR} enden",
            args.join(" ")
        );
    }
}
