---
title: Hell/Dunkel folgt nur dem System
datum: 2026-11-27
betrifft: docs/arc42/08-konzepte/K-012-design-system-und-barrierefreiheit.md
art: änderung
status: angenommen und in docs/ umgesetzt
---

## Beobachtung
K-012 Abschnitt 1 sagt: „der Modus folgt dem System, eine manuelle Umschaltung ist offen“. In der Session zu #105 (2026-11-27) hat der Product Owner entschieden, dass es keinen Schalter gibt: Das Frontend wählt den Modus nur über `prefers-color-scheme` und speichert keine Wahl. Ein Schalter wäre eine eigene Story. Ticket #105 ist entsprechend angepasst.

## Vorschlag
In K-012 Abschnitt 1, letzter Punkt:

> Im Frontend (ADR-007) werden die Tokens als CSS-Variablen bereitgestellt; der Modus folgt nur dem System (`prefers-color-scheme`), ohne Schalter und ohne gespeicherte Wahl (Entscheidung des Product Owners, 2026-11-27). Ein Schalter wäre eine eigene Story.

## Wirkung
- #105: Der Punkt „Entscheidung Hell/Dunkel“ entfällt, der Task für die CSS-Variablen deckt die Moduswahl ab.
- Kein UI-Element, kein Wireframe, keine gespeicherten Daten für den Modus.

## Entscheidung (Mensch)
- 2026-11-27 (Product Owner): angenommen. Umgesetzt in `docs/`: K-012 Abschnitt 1, letzter Punkt, wie vorgeschlagen.
