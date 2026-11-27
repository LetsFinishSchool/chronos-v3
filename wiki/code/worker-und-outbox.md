---
title: Worker und Outbox-Abarbeitung
type: code
sources:
  - issue:#102
  - docs/arc42/09-entscheidungen/ADR-002-zerlegung-monolith-plus-worker.md
  - docs/arc42/08-konzepte/K-003-ereignisse-und-benachrichtigung.md
  - docs/arc42/05-bausteine/02-crate-zuschnitt.md
  - deny.toml
  - crates/core/src/outbox.rs
  - crates/core/src/consumer.rs
  - crates/worker/src/runner.rs
  - crates/chronos/tests/worker/main.rs
  - crates/chronos/tests/cli.rs
confidence: hoch
last-verified: 2026-11-27
---

# Worker und Outbox-Abarbeitung

## Aufteilung auf Crates
- **`chronos-core`** (`outbox.rs`, `consumer.rs`): `Outbox::process_batch`, Trait `Consumer`, `ConsumerRegistry`, `OutboxEvent`. Hier liegt das SQL, weil `sqlx` laut ADR-009 und `deny.toml` nur in `core`, `domain` und `chronos` vorkommen darf. Kapitel 5 nennt die Abarbeitung beim Worker; das ist als Vorschlag gemeldet (`proposals/2026-11-27-outbox-abarbeitung-in-core.md`).
- **`chronos-worker`**: `run` (Schleife, Taktung, Stopp), `WorkerConfig`, `LogConsumer`. Kein `sqlx`.
- **`chronos`** (`main.rs`): `chronos worker` = Schemaprüfung (`ensure_schema`, Exit 75), Logging, Signale, Konfiguration, `run`. `CHRONOS_WORKER_LOG_EVENTS` (kommagetrennt) registriert den `LogConsumer` für diese Ereignisarten; `cli.rs` belegt den Weg im echten Prozess mit `cli.test`. Sonst ist die Registry leer: Es gibt keine Fachereignisse, also gilt jedes Ereignis als „ohne Verbraucher“.

## Verhalten
- **Je Ereignis eine Transaktion:** `SELECT … WHERE processed_at IS NULL AND id > $cursor ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED`, Verbraucher, `UPDATE processed_at`, Commit. Ein Verbraucherfehler rollt zurück; das Ereignis bleibt unverarbeitet.
- **Cursor `id > $1` ist nötig:** Ohne ihn käme ein fehlgeschlagenes Ereignis in derselben Charge sofort wieder an die Reihe (Endlosschleife). Der Cursor gilt nur innerhalb einer Charge; die nächste beginnt wieder bei 0 und versucht Fehlgeschlagene erneut.
- **Charge = bis zu N *erfolgreich* verarbeitete Ereignisse.** Eine Charge voll fehlgeschlagener Ereignisse gilt nie als voll, sonst gäbe es kein Warten zwischen den Versuchen (Heißschleife). Voll (`processed >= batch_size`) bedeutet: sofort die nächste Charge, sonst `poll_interval` warten.
- **Ohne Verbraucher:** Warnung mit `event_id`, `event`, `correlation_id`, dann als verarbeitet markiert.
- **Panic im Verbraucher:** läuft in eigener Task (`tokio::spawn`) und zählt wie ein `Err`; sonst stürzte ein Giftereignis den Worker bei jedem Neustart ab.
- **Verbraucher bekommen keine Datenbankverbindung.** Der Worker ändert Fachdaten nur über Operationen (Kapitel 5); ein Verbraucher, der in derselben Transaktion schreiben muss, ist ein Thema für #23. Deshalb ist „Aufruf und Markierung in einer Transaktion“ hier nur die Sperre plus Markierung nach `Ok`.
- **Stopp:** `CancellationToken`. `run` prüft vor jeder Charge und unterbricht nur das Warten, nie eine laufende Charge. `chronos worker` löst bei SIGTERM und SIGINT aus und endet mit Exit-Code 0.
- **Konfiguration:** `CHRONOS_WORKER_POLL_MS` (Standard 2000, größer 0), `CHRONOS_WORKER_BATCH_SIZE` (Standard 50, größer 0).
- **Logging:** `tracing` mit JSON auf stderr, Stufe über `RUST_LOG` (Standard `info`). Korrelations-ID steht als Feld `correlation_id` in jedem Ereignis-Log. Nutzdaten (`payload`) bleiben aus dem Log (K-009).
- **Bewusste Lücke (aus dem Ticket):** kein Wiederholungslimit, keine Wartezeit zwischen Versuchen, keine Behandlung dauerhaft fehlschlagender Ereignisse; gehört zu #23.

## Tests (`crates/chronos/tests/worker/`, `tests/cli.rs`)
- Ein Test nutzt die Beispieloperation aus `tests/operationsrahmen/beispiel.rs` per `#[path]` (Ereignis → Worker-Log mit gleicher `correlation_id`).
- Absturz: `JoinHandle::abort` auf einen Worker, dessen Verbraucher blockiert; die Transaktion wird beim Drop zurückgerollt (Rollback beim Drop, kein echter Verbindungsabbruch), die Sperre fällt asynchron, deshalb wiederholt der Test die Charge bis zu 5 s.
- Zwei Worker: ein blockierender Verbraucher hält Ereignis 1, ein zweiter Worker verarbeitet nur die übrigen. Ohne `SKIP LOCKED` hängt dieser Test (Gegenprobe gemacht).
- `cli.rs` startet den echten Prozess, prüft mit der Rolle `chronos_app`, dass `UPDATE` auf `outbox` erlaubt ist, und sendet SIGTERM über `kill -TERM` (`unsafe` ist verboten). Es gibt **einen** Test für alles, weil alle Prozess-Worker dieselbe gemeinsame Datenbank abarbeiten und sich sonst gegenseitig die Ereignisse wegnehmen.

## Stolpersteine
- **Rootless Docker (pasta):** Port 54329 war nicht erreichbar. Postgres mit gemountetem Socket-Verzeichnis starten; der Pfad muss **kurz** sein (`SUN_LEN`, etwa 108 Zeichen), das Scratchpad-Verzeichnis war zu lang, `/tmp/pg102` ging. Mehr in `code/datenbank-und-migrationen.md`.
- `cargo update -w` (ohne `--locked`) nach jeder neuen Abhängigkeit, sonst bricht schon `cargo nextest` ab.
- `pkill -f` mit Muster aus dem eigenen Befehl beendet die eigene Shell.
