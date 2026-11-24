# Spike E-002: Ergebnisse der vier Sprachen

Orphan-Branch `spikes/e-002-ergebnisse` (keine gemeinsame Historie mit `main`).
Je Unterordner das Ergebnis einer Sprache (`go`, `python`, `rust`, `typescript`) mit der
ursprünglichen Commit-Historie; Pfade in der Historie sind mit dem Sprachordner präfixiert.
Ohne `node_modules`, `target/` und `.stack/`. Werkzeuge, Abnahmetests und Referenz
liegen in `main` unter `spikes/e-002/`. Entscheidung: ADR-004.

Auschecken: `git worktree add ../chronos-spikes spikes/e-002-ergebnisse`
