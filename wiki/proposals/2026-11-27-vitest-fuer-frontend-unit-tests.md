---
title: Vitest für Unit-Tests im Frontend
datum: 2026-11-27
betrifft: docs/arc42/09-entscheidungen/ADR-009-teststrategie-und-architekturregeln.md
art: neu
status: angenommen und in docs/ umgesetzt
---

## Beobachtung
ADR-009 nennt für das Frontend nur Ebene 6 (Playwright und axe-core). Für Unit-Tests ohne Browser fehlt ein Werkzeug. Der erste Fall ist der Tokentest #106 (Kontrast von `designs/tokens/tokens.json`). In der Session zu #105 (2026-11-27) hat der Product Owner Vitest gewählt. Die Alternativen waren `node --test` (ohne Abhängigkeit) und Python mit Standardbibliothek. Ticket #106 ist entsprechend angepasst.

## Vorschlag
In ADR-009 bei Ebene 1 (Unit-Tests im Modul) ergänzen:

> Im Frontend laufen Unit-Tests mit Vitest (Entwicklungsabhängigkeit, exakte Version, npm-Skript `test:unit`), im CI-Job `frontend`.

## Wirkung
- #106 legt Vitest an; spätere Unit-Tests im Frontend nutzen es.
- Neue Entwicklungsabhängigkeit in der npm-Lieferkette (ADR-013, `npm audit`).

## Entscheidung (Mensch)
- 2026-11-27 (Product Owner): angenommen. Umgesetzt in `docs/`: ADR-009, Testebene 1, wie vorgeschlagen.
