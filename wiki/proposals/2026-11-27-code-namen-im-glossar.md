---
title: Englische Code-Namen im Glossar ergänzen
datum: 2026-11-27
betrifft: docs/req42/08-terminologie/glossar.md
art: änderung
status: offen   # Mensch setzt: angenommen | abgelehnt | zurückgestellt
---

## Beobachtung
`docs/README.md` Regel 4 und Kapitel 2 verlangen englische Code-Namen „(Zuordnung: Glossar)“. In #101 entstanden neue Begriffe, deren Code-Name im Glossar fehlt. Das Ticket #101 selbst nannte die Tabellen und Spalten deutsch (`verlauf`, `person (Kennung, Art)`); umgesetzt wurden englische Namen (`crates/core`, Migration `20261125010000_operation_frame.sql`).

## Vorschlag
Glossar um diese Zeilen in der Spalte „Code-Name“ ergänzen:

| Begriff | Code-Name |
|---|---|
| Verlauf | `history` |
| Verlaufseintrag | `history` (Tabelle), Spalten `action`, `object_kind`, `object_id`, `before` |
| Korrelations-ID | `correlation_id` |
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
Nur Dokumentation. Offene Tickets, die deutsche Tabellen- oder Spaltennamen nennen (z. B. #34 Verlauf), sollten die englischen Namen übernehmen.

## Entscheidung (Mensch)
