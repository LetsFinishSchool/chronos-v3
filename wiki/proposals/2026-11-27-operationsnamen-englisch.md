---
title: Operationsnamen im Muster `area.verb` statt `bereich.verb`
datum: 2026-11-27
betrifft: docs/arc42/09-entscheidungen/ADR-005-operationsschicht.md, docs/arc42/09-entscheidungen/E-005-operationsschicht-analyse.md
art: änderung
status: angenommen   # Product Owner, 2026-11-27
---

## Beobachtung
`docs/` verlangt englische Code-Namen (`docs/arc42/02-randbedingungen/01-randbedingungen.md`, Glossar). ADR-005 (Festlegung 7) und E-005 beschreiben das Namensmuster der Operationen aber als `bereich.verb`. Das Muster ist nur eine Bezeichnung, die Beispiele (`team.create`) sind englisch. Ticket #101 nennt es jetzt `area.verb`.

## Vorschlag
In ADR-005 und E-005 „`bereich.verb`“ durch „`area.verb` (Fachbereich, Verb)“ ersetzen.

## Wirkung
Nur Wortlaut in `docs/`; Code, Tests und Tickets sind bereits englisch benannt.

## Entscheidung (Mensch)
Angenommen am 2026-11-27 (Product Owner im Gespräch); `docs/` angepasst.
