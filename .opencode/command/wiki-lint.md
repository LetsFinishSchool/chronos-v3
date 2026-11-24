---
description: Wiki prüfen (tote Links, fehlende Quellen, veraltet, Widersprüche zu docs/)
---
Führe nach `wiki/README.md` (Abschnitt Lint) eine Prüfung von `wiki/` durch: tote Links, Seiten ohne `sources`, altes `last-verified`, verwaiste Seiten, Widersprüche zu `docs/`. Offensichtliches reparieren, den Rest als Bericht nach `wiki/status/<Datum>-lint.md` schreiben und in `wiki/log.md` vermerken. Zusätzlich prüfen: Enthält `docs/` Verweise auf `wiki/` (`grep -rn wiki docs`)? Das ist ein Regelverstoß (AGENTS.md, Verweisrichtung) und als Vorschlag zu melden. `docs/` nicht ändern.
