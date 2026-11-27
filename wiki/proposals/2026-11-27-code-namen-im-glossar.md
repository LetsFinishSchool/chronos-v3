---
title: Englische Code-Namen im Glossar ergänzen
datum: 2026-11-27
betrifft: docs/req42/08-terminologie/glossar.md
art: änderung
status: offen   # Mensch setzt: angenommen | abgelehnt | zurückgestellt
---

## Beobachtung
`docs/README.md` Regel 4 und Kapitel 2 verlangen englische Code-Namen „(Zuordnung: Glossar)“. In #101 entstanden neue Begriffe, deren Code-Name im Glossar fehlt. Das Ticket #101 nannte zunächst deutsche Tabellen und Spalten (`verlauf`, `person (Kennung, Art)`) und wurde am 2026-11-27 auf englische Namen umgestellt; umgesetzt sind sie in `crates/core` und der Migration `20261125010000_operation_frame.sql`.

## Vorschlag
Glossar um diese Zeilen in der Spalte „Code-Name“ ergänzen:

| Begriff | Code-Name |
|---|---|
| Verlauf | `history` |
| Verlaufseintrag | `history` (Tabelle), Spalten `action`, `object_kind`, `object_id`, `before` |
| Korrelations-ID | `correlation_id` |
| Vorher-Zustand | `previous_state` |
| Bündel-ID | `bundle_id` |
| Akteur | `actor` (`actor_id`, `ActorKind`) |
| Outbox | `outbox` |
| Ereignis | `event` |
| Operation | `operation` |
| Geltungsbereich | `scope` |
| Probelauf | `dry run` (`Run::DryRun`) |
| Rahmen | `frame` (`Frame`) |
| Person / Gast (Art des Akteurs) | `person` / `guest` |

Außerdem Regel 4 in `docs/README.md` um einen Satz ergänzen: „Das gilt für Bezeichner im Code, Tabellen, Spalten, Parameter und Fehlercodes.“

## Wirkung
Nur Dokumentation. Geprüft wurden alle Tickets auf deutsche Code-Namen in Backticks; außer #101 (bereits angepasst) gab es keine. #34 (Verlauf) nennt keine Spaltennamen und sollte bei der Konkretisierung die englischen aus #101 übernehmen.

## Entscheidung (Mensch)
