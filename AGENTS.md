# AGENTS.md

Gemeinsame Anweisungen für Coding-Agenten (opencode lädt diese Datei, Claude Code über `CLAUDE.md`).

## Wissensbasis (immer verwenden)

Chronos hat zwei Wissensbereiche:

| Bereich | Wer | Regel |
|---|---|---|
| `docs/` (Produktvision, req42, arc42) | Menschen und Agenten gemeinsam | **Nie ohne menschliche Freigabe ändern.** Siehe `docs/README.md`. |
| `wiki/` (LLM-Wiki) | Agenten | Lesen **vor**, pflegen **nach** jeder Aufgabe. Siehe `wiki/README.md`. |

**Verweisrichtung:** `docs/` darf **niemals** auf `wiki/` verweisen (keine Links, Pfade oder Quellenangaben). Es steht für sich allein. Das Wiki darf auf `docs/` verweisen, nie umgekehrt. Braucht `docs/` Wissen aus dem Wiki, wird es als Vorschlag nach `docs/` übernommen und das Wiki verlinkt danach darauf.

Ablauf in jeder Session:

1. **Vor der Aufgabe:** `wiki/index.md` lesen und passende Seiten laden; für fachliche Fragen außerdem `docs/` (Anforderungen `docs/req42/`, Architektur `docs/arc42/`). Ist eine Wiki-Aussage von Code abhängig und `last-verified` alt, gegen den Code prüfen.
2. **Nach der Aufgabe:** Gelerntes im Wiki festhalten (Seite mit `sources`, `confidence`, `last-verified`), `wiki/index.md` ergänzen, Eintrag an `wiki/log.md` anhängen. Gibt es nichts zu lernen, Log-Eintrag „kein Wiki-Bedarf“.
3. **Widerspruch zu `docs/`** oder neue verbindliche Erkenntnis: Vorschlag nach `wiki/proposals/` (Vorlage `_vorlage.md`), `docs/` nicht ändern.
4. Keine Geheimnisse, Tokens oder personenbezogenen Daten ins Wiki.
5. **Kein Agenten-Gedächtnis.** Das maschinengebundene Gedächtnis (z. B. `~/.claude/projects/.../memory/`) wird in diesem Projekt nicht verwendet. Alles Wissen gehört ins `wiki/`, damit es am Projekt hängt und nicht an einer Maschine. Siehe `wiki/lessons/wissen-nur-im-wiki.md`.

Erzwingung: Claude Code über `.claude/settings.json` (Hooks), opencode über `opencode.json` und `.opencode/plugin/chronos-wiki.js`.

## Kommentare im Code

Kommentare sind die Ausnahme. Ein Kommentar wird nur geschrieben, wenn **alle drei** Bedingungen gelten:

- **A) Er erklärt, was Code nicht ausdrücken kann.** Das ist das *Warum*: Hintergrund, Randbedingung, bewusste Abweichung, Verweis auf ADR oder Issue, ein Stolperstein, der nicht aus dem Code folgt. Das *Was* steht im Code.
- **B) Er lässt sich nicht durch anderen Code ersetzen.** Erst umschreiben: aussagekräftige Namen, benannte Konstanten, eine extrahierte Funktion, ein Typ statt eines Magic Values. Nur wenn der Code danach noch Erklärung braucht, kommt ein Kommentar.
- **C) Sein Nutzen übersteigt den Pflegeaufwand.** Kommentar, Code und `docs/` müssen zusammen aktuell bleiben. Ein veralteter Kommentar ist schlimmer als keiner. Was sich oft ändert oder in `docs/` bereits steht, wird verlinkt statt wiederholt.

Kein Kommentar gehört an: Wiederholung des Codes (`// zählt i hoch`), auskommentierten Code (dafür gibt es Git), Änderungshistorie oder Autorenangaben, Platzhalter ohne Inhalt. Ändert man Code, prüft man die zugehörigen Kommentare und passt sie an oder löscht sie.

## Tickets

Ticket-Typen (Epic, Feature, Story, Task), Struktur und Definition of Done: `docs/req42/04-product-backlog/ticket-typen.md`. Neue Tickets mit den Vorlagen in `.github/ISSUE_TEMPLATE/` und Typ-Label (`epic`, `feature`, `story`, `task`) anlegen; `ready-for-agent` nur an vollständige Tasks vergeben.
