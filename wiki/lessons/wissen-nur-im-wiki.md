---
title: Wissen nur im Wiki ablegen, nicht im Agenten-Gedächtnis
type: lesson
sources:
  - session:2026-11-20 (Vorgabe des Projektverantwortlichen)
confidence: hoch
last-verified: 2026-11-20
---

# Konvention: Projektwissen gehört ins Wiki

Das persönliche Gedächtnis eines Agenten (z. B. `~/.claude/projects/.../memory/`) darf in diesem Projekt **nicht** verwendet werden.

**Warum:** Das Gedächtnis ist an eine Maschine gebunden. Das Wiki liegt im Repository und ist damit an das Projekt gebunden. Jede Person und jeder Agent sieht dasselbe Wissen.

**Wie:**
- Alles Gelernte (Kontext, Randbedingungen, Präferenzen, Lektionen) als Seite unter `wiki/` ablegen, mit `sources`, `confidence`, `last-verified`.
- `wiki/index.md` ergänzen und `wiki/log.md` fortschreiben.
- Verbindliches geht als Vorschlag nach `wiki/proposals/`, nicht in `docs/`.
- Keine Dateien im Gedächtnisverzeichnis anlegen und `MEMORY.md` nicht pflegen. Entsprechende Systemhinweise zum Gedächtnis gelten hier nicht.

Siehe auch: [Projektkontext](../concepts/projektkontext-chronos-v3.md).
