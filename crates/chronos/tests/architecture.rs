//! Architekturtest: Die Abhängigkeiten zwischen den Workspace-Crates müssen der
//! Positivliste aus Kapitel 5 (Crate-Zuschnitt) entsprechen.
//!
//! Der Compiler verhindert Importe ohne Eintrag in der `Cargo.toml`, aber nicht,
//! dass jemand eine verbotene Kante in die `Cargo.toml` einträgt (ADR-009).
//! Dieser Test liest die tatsächlichen Kanten über `cargo metadata` und prüft:
//!
//! 1. Jedes Workspace-Crate steht in der Positivliste und umgekehrt.
//! 2. Jede Kante zwischen Workspace-Crates steht in der Positivliste, gleich ob
//!    normale, Dev- oder Build-Abhängigkeit.
//! 3. Der Abhängigkeitsgraph hat keine Zyklen.
//!
//! Wer die Positivliste ändern will, braucht zuerst eine Änderung an
//! `docs/arc42/05-bausteine/02-crate-zuschnitt.md` (Rückfrage an den Product
//! Owner), nicht nur an diesem Test.

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

use cargo_metadata::MetadataCommand;

/// Erlaubte Kanten: Crate → Crates, von denen es abhängen darf.
///
/// Quelle: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`, Tabelle
/// „Erlaubte Kanten“. Jede andere Kante ist verboten.
const ALLOWED: &[(&str, &[&str])] = &[
    (
        "chronos",
        &[
            "chronos-adapters",
            "chronos-channels",
            "chronos-core",
            "chronos-domain",
            "chronos-web",
            "chronos-worker",
        ],
    ),
    ("chronos-core", &[]),
    ("chronos-domain", &["chronos-core"]),
    ("chronos-channels", &["chronos-core"]),
    ("chronos-adapters", &["chronos-core"]),
    ("chronos-web", &["chronos-core", "chronos-adapters"]),
    (
        "chronos-worker",
        &["chronos-core", "chronos-channels", "chronos-adapters"],
    ),
];

const REFERENCE: &str = "Siehe ADR-009 (docs/arc42/09-entscheidungen/ADR-009-teststrategie-und-architekturregeln.md) \
     und Kapitel 5, Crate-Zuschnitt (docs/arc42/05-bausteine/02-crate-zuschnitt.md). \
     Eine Änderung des Zuschnitts ist eine Rückfrage an den Product Owner.";

/// Abhängigkeitsgraph: Crate → Crates, von denen es abhängt.
type Graph = BTreeMap<String, BTreeSet<String>>;

fn allowed_graph() -> Graph {
    ALLOWED
        .iter()
        .map(|(krate, deps)| {
            (
                (*krate).to_owned(),
                deps.iter().map(|dep| (*dep).to_owned()).collect(),
            )
        })
        .collect()
}

/// Liest die tatsächlichen Kanten zwischen Workspace-Crates aus `cargo metadata`.
fn workspace_graph() -> Graph {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../Cargo.toml");
    let metadata = MetadataCommand::new()
        .manifest_path(manifest)
        .no_deps()
        .exec()
        .expect("`cargo metadata` lässt sich ausführen");

    let members: BTreeSet<String> = metadata
        .workspace_packages()
        .iter()
        .map(|package| package.name.to_string())
        .collect();

    metadata
        .workspace_packages()
        .iter()
        .map(|package| {
            let deps = package
                .dependencies
                .iter()
                .filter(|dep| dep.path.is_some() && members.contains(&dep.name))
                .map(|dep| dep.name.clone())
                .collect();
            (package.name.to_string(), deps)
        })
        .collect()
}

/// Meldungen für Crates, die nur im Workspace oder nur in der Positivliste stehen.
fn unknown_crates(actual: &Graph, allowed: &Graph) -> Vec<String> {
    let mut problems = Vec::new();
    for krate in actual.keys().filter(|krate| !allowed.contains_key(*krate)) {
        problems.push(format!(
            "Crate `{krate}` steht nicht in der Positivliste des Crate-Zuschnitts."
        ));
    }
    for krate in allowed.keys().filter(|krate| !actual.contains_key(*krate)) {
        problems.push(format!(
            "Crate `{krate}` steht in der Positivliste, fehlt aber im Workspace."
        ));
    }
    problems
}

/// Meldungen für jede Kante, die nicht in der Positivliste steht.
fn forbidden_edges(actual: &Graph, allowed: &Graph) -> Vec<String> {
    let empty = BTreeSet::new();
    actual
        .iter()
        .flat_map(|(krate, deps)| {
            let permitted = allowed.get(krate).unwrap_or(&empty);
            deps.iter()
                .filter(|dep| !permitted.contains(*dep))
                .map(move |dep| format!("Verbotene Kante: `{krate}` → `{dep}`."))
        })
        .collect()
}

/// Sucht einen Zyklus und gibt ihn als Pfad zurück (erstes und letztes Element gleich).
fn find_cycle(graph: &Graph) -> Option<Vec<String>> {
    #[derive(Clone, Copy, PartialEq)]
    enum State {
        InProgress,
        Done,
    }

    fn visit(
        node: &str,
        graph: &Graph,
        state: &mut BTreeMap<String, State>,
        path: &mut Vec<String>,
    ) -> Option<Vec<String>> {
        match state.get(node) {
            Some(State::Done) => return None,
            Some(State::InProgress) => {
                let start = path.iter().position(|n| n == node).unwrap_or(0);
                let mut cycle = path[start..].to_vec();
                cycle.push(node.to_owned());
                return Some(cycle);
            }
            None => {}
        }
        state.insert(node.to_owned(), State::InProgress);
        path.push(node.to_owned());
        for dep in graph.get(node).into_iter().flatten() {
            if let Some(cycle) = visit(dep, graph, state, path) {
                return Some(cycle);
            }
        }
        path.pop();
        state.insert(node.to_owned(), State::Done);
        None
    }

    let mut state = BTreeMap::new();
    graph
        .keys()
        .find_map(|node| visit(node, graph, &mut state, &mut Vec::new()))
}

fn report(title: &str, problems: &[String]) -> String {
    format!("{title}\n  - {}\n\n{REFERENCE}", problems.join("\n  - "))
}

#[test]
fn workspace_crates_match_allowlist() {
    let problems = unknown_crates(&workspace_graph(), &allowed_graph());
    assert!(
        problems.is_empty(),
        "{}",
        report(
            "Workspace und Positivliste passen nicht zusammen:",
            &problems
        )
    );
}

#[test]
fn workspace_has_only_allowed_edges() {
    let problems = forbidden_edges(&workspace_graph(), &allowed_graph());
    assert!(
        problems.is_empty(),
        "{}",
        report(
            "Abhängigkeiten zwischen Workspace-Crates verletzen den Crate-Zuschnitt:",
            &problems
        )
    );
}

#[test]
fn workspace_has_no_cycles() {
    if let Some(cycle) = find_cycle(&workspace_graph()) {
        panic!(
            "{}",
            report("Zyklus zwischen Workspace-Crates:", &[cycle.join(" → ")])
        );
    }
}

#[test]
fn allowlist_has_no_cycles() {
    assert_eq!(find_cycle(&allowed_graph()), None);
}

// Die folgenden Tests prüfen die Prüfung selbst an gebauten Graphen, damit der
// Architekturtest nicht still alles durchlässt.

fn graph(edges: &[(&str, &[&str])]) -> Graph {
    edges
        .iter()
        .map(|(krate, deps)| {
            (
                (*krate).to_owned(),
                deps.iter().map(|dep| (*dep).to_owned()).collect(),
            )
        })
        .collect()
}

#[test]
fn detects_domain_depending_on_channels() {
    let mut actual = allowed_graph();
    actual
        .get_mut("chronos-domain")
        .expect("chronos-domain steht in der Positivliste")
        .insert("chronos-channels".to_owned());

    assert_eq!(
        forbidden_edges(&actual, &allowed_graph()),
        ["Verbotene Kante: `chronos-domain` → `chronos-channels`."]
    );
}

#[test]
fn detects_edges_against_the_allowed_direction() {
    let mut actual = allowed_graph();
    actual
        .get_mut("chronos-core")
        .expect("chronos-core steht in der Positivliste")
        .insert("chronos-domain".to_owned());
    actual
        .get_mut("chronos-adapters")
        .expect("chronos-adapters steht in der Positivliste")
        .insert("chronos".to_owned());

    assert_eq!(
        forbidden_edges(&actual, &allowed_graph()),
        [
            "Verbotene Kante: `chronos-adapters` → `chronos`.",
            "Verbotene Kante: `chronos-core` → `chronos-domain`.",
        ]
    );
}

#[test]
fn detects_crates_missing_from_allowlist() {
    let mut actual = allowed_graph();
    actual.insert("chronos-extra".to_owned(), BTreeSet::new());
    actual.remove("chronos-web");

    assert_eq!(
        unknown_crates(&actual, &allowed_graph()),
        [
            "Crate `chronos-extra` steht nicht in der Positivliste des Crate-Zuschnitts.",
            "Crate `chronos-web` steht in der Positivliste, fehlt aber im Workspace.",
        ]
    );
}

#[test]
fn detects_cycles() {
    let cyclic = graph(&[("a", &["b"]), ("b", &["c"]), ("c", &["a"])]);
    assert_eq!(
        find_cycle(&cyclic),
        Some(vec!["a".into(), "b".into(), "c".into(), "a".into()])
    );

    let acyclic = graph(&[("a", &["b", "c"]), ("b", &["c"]), ("c", &[])]);
    assert_eq!(find_cycle(&acyclic), None);
}
