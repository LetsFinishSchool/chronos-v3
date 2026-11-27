//! Architekturtest: Die Abhängigkeiten zwischen den Workspace-Crates müssen der
//! Positivliste aus dem Crate-Zuschnitt entsprechen (ADR-009).
//!
//! Der Compiler verhindert Importe ohne Eintrag in der `Cargo.toml`, aber nicht
//! eine verbotene Kante in der `Cargo.toml` selbst.

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

use cargo_metadata::MetadataCommand;

/// Quelle: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`, Tabelle „Erlaubte Kanten“.
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

const REFERENCE: &str = "See ADR-009 (docs/arc42/09-entscheidungen/ADR-009-teststrategie-und-architekturregeln.md) \
     and chapter 5, crate layout (docs/arc42/05-bausteine/02-crate-zuschnitt.md). \
     Changing the layout needs the Product Owner.";

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

fn workspace_graph() -> Graph {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../Cargo.toml");
    let metadata = MetadataCommand::new()
        .manifest_path(manifest)
        .no_deps()
        .exec()
        .expect("`cargo metadata` can run");

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

fn unknown_crates(actual: &Graph, allowed: &Graph) -> Vec<String> {
    let mut problems = Vec::new();
    for krate in actual.keys().filter(|krate| !allowed.contains_key(*krate)) {
        problems.push(format!(
            "Crate `{krate}` is not in the allowlist of the crate layout."
        ));
    }
    for krate in allowed.keys().filter(|krate| !actual.contains_key(*krate)) {
        problems.push(format!(
            "Crate `{krate}` is in the allowlist but missing from the workspace."
        ));
    }
    problems
}

fn forbidden_edges(actual: &Graph, allowed: &Graph) -> Vec<String> {
    let empty = BTreeSet::new();
    actual
        .iter()
        .flat_map(|(krate, deps)| {
            let permitted = allowed.get(krate).unwrap_or(&empty);
            deps.iter()
                .filter(|dep| !permitted.contains(*dep))
                .map(move |dep| format!("Forbidden edge: `{krate}` → `{dep}`."))
        })
        .collect()
}

/// Pfad eines Zyklus; erstes und letztes Element sind gleich.
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
        report("Workspace and allowlist do not match:", &problems)
    );
}

#[test]
fn workspace_has_only_allowed_edges() {
    let problems = forbidden_edges(&workspace_graph(), &allowed_graph());
    assert!(
        problems.is_empty(),
        "{}",
        report(
            "Dependencies between workspace crates violate the crate layout:",
            &problems
        )
    );
}

#[test]
fn workspace_has_no_cycles() {
    if let Some(cycle) = find_cycle(&workspace_graph()) {
        panic!(
            "{}",
            report("Cycle between workspace crates:", &[cycle.join(" → ")])
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
        .expect("chronos-domain is in the allowlist")
        .insert("chronos-channels".to_owned());

    assert_eq!(
        forbidden_edges(&actual, &allowed_graph()),
        ["Forbidden edge: `chronos-domain` → `chronos-channels`."]
    );
}

#[test]
fn detects_edges_against_the_allowed_direction() {
    let mut actual = allowed_graph();
    actual
        .get_mut("chronos-core")
        .expect("chronos-core is in the allowlist")
        .insert("chronos-domain".to_owned());
    actual
        .get_mut("chronos-adapters")
        .expect("chronos-adapters is in the allowlist")
        .insert("chronos".to_owned());

    assert_eq!(
        forbidden_edges(&actual, &allowed_graph()),
        [
            "Forbidden edge: `chronos-adapters` → `chronos`.",
            "Forbidden edge: `chronos-core` → `chronos-domain`.",
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
            "Crate `chronos-extra` is not in the allowlist of the crate layout.",
            "Crate `chronos-web` is in the allowlist but missing from the workspace.",
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

/// Crates, die Fachbereiche nicht erreichen dürfen (Regel 2, ADR-005): Fachbereiche erzeugen
/// nur Ereignisse und kennen keine Nachbarsysteme, Kanäle oder Prozesse.
const UNREACHABLE_FROM_DOMAIN: &[&str] = &[
    "chronos-adapters",
    "chronos-channels",
    "chronos-web",
    "chronos-worker",
];

/// Bausteine, mit denen Fachcode selbst eine Verbindung oder Transaktion beschaffen könnte.
/// Eine Verbindung bekommt er nur über den `Context` des Rahmens.
const DATABASE_ACCESS_BYPASSES: &[&str] = &[
    "PgPool",
    "PgPoolOptions",
    "PgConnectOptions",
    "sqlx::Pool",
    "Connection::connect",
    "connect_lazy",
    ".begin(",
    "chronos_core::db",
    "Context::new",
];

fn bypasses_in(source: &str) -> Vec<&'static str> {
    DATABASE_ACCESS_BYPASSES
        .iter()
        .copied()
        .filter(|bypass| source.contains(bypass))
        .collect()
}

fn rust_files(directory: &Path) -> Vec<std::path::PathBuf> {
    let mut files = Vec::new();
    for entry in std::fs::read_dir(directory).expect("directory is readable") {
        let path = entry.expect("entry is readable").path();
        if path.is_dir() {
            files.extend(rust_files(&path));
        } else if path.extension().is_some_and(|extension| extension == "rs") {
            files.push(path);
        }
    }
    files
}

#[test]
fn domain_does_not_reach_adapters() {
    let graph = workspace_graph();
    let reached: Vec<String> = graph["chronos-domain"]
        .iter()
        .filter(|dep| UNREACHABLE_FROM_DOMAIN.contains(&dep.as_str()))
        .cloned()
        .collect();
    assert!(
        reached.is_empty(),
        "{}",
        report(
            "Domain modules reach adapters, channels or processes:",
            &reached
        )
    );
}

#[test]
fn domain_gets_no_database_connection_without_the_frame() {
    let sources = Path::new(env!("CARGO_MANIFEST_DIR")).join("../domain/src");
    let problems: Vec<String> = rust_files(&sources)
        .into_iter()
        .flat_map(|file| {
            let source = std::fs::read_to_string(&file).expect("source file is readable");
            bypasses_in(&source)
                .into_iter()
                .map(|bypass| format!("{} uses `{bypass}`", file.display()))
                .collect::<Vec<_>>()
        })
        .collect();
    assert!(
        problems.is_empty(),
        "{}",
        report(
            "Domain modules bypass the frame (connections only via the Context):",
            &problems
        )
    );
}

#[test]
fn detects_database_access_bypasses() {
    assert_eq!(
        bypasses_in("fn run(ctx: &mut Context) {}"),
        Vec::<&str>::new()
    );
    assert_eq!(
        bypasses_in("let pool: PgPool = db::connect(url);"),
        vec!["PgPool"]
    );
    assert_eq!(
        bypasses_in("let tx = pool.begin().await?;"),
        vec![".begin("]
    );
    assert_eq!(
        bypasses_in("use chronos_core::db::connect;"),
        vec!["chronos_core::db"]
    );
}
