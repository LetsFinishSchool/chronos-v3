# Wiki-Index

Agenten: zuerst hier lesen. Eine Zeile pro Seite, nach Typ gruppiert. Pflichtpflege bei jedem Ingest.

## Konzepte
- [E-002 Spike: Lehren](concepts/e-002-spike-ergebnisse.md): Lehren für künftige Agentenläufe (Ergebnisse in ADR-004)
- [C4-Diagramme zu arc42](concepts/c4-diagramme-arc42.md): Excalidraw-Diagramme (Kontext, Container, Komponenten, Laufzeit, Verteilung) in `docs/arc42/diagramme/` (Generator in `docs/arc42/diagramme/generator/`), Lücken der Zeichnung
- [Farb- und Token-System](concepts/farb-und-token-system.md): Purple-Schema, Textstile, Schatten, Verläufe; WCAG-AA-Anpassungen und Prüfstand; Datei `designs/tokens/tokens.json` (kein Figma-Export im Repo)
- [Worktrees: .env und .envrc übernehmen](concepts/worktree-dateien-uebernehmen.md): herdr kopiert keine gitignorierten Dateien; Hook `.githooks/post-checkout` liest `.worktreekeep`
- [req42-Backlog und GitHub-Issues](concepts/req42-anforderung-vs-feature-und-tickets.md): FA/F-Unterschied, Überführung in 91 Issues, Anpassungen, Stolpersteine
- [sqlx und das rsa-Advisory](concepts/sqlx-und-rsa-advisory.md): sqlx 0.8 bringt `rsa` in die Lockdatei, 0.9.1 nicht; Entscheidung für 0.9 in #100
- [Crate-Zuschnitt (Diagramm)](diagramme/crate-zuschnitt.excalidraw): sieben Crates mit erlaubten und verbotenen Kanten zu `docs/arc42/05-bausteine/02-crate-zuschnitt.md` (Excalidraw, SVG-Vorschau, Skript `crate-zuschnitt.py`)

## Code
- [Cargo-Workspace und Architekturtest](code/cargo-workspace.md): Aufbau des Workspace, Binary `chronos` (`serve` mit axum, `/healthz`, Graceful Shutdown seit #113), Architekturtest mit Positivliste, Stolperstellen (Exit-Code 2 gehört clap, 69 seit #102 nicht mehr vergeben; Zyklen über Dev-Abhängigkeiten; ungenutzte Abhängigkeiten ab Cargo 1.100), Prüfbefehle
- [CI und Lieferkettenprüfung](code/ci-und-lieferkette.md): Workflow mit vier Jobs, `deny.toml`, Ablaufskript, Dependabot, Stolpersteine
- [Worker und Outbox-Abarbeitung](code/worker-and-outbox.md): Aufteilung core/worker/chronos, Cursor und Chargenbegriff, Stopp, Konfiguration, Logging, Tests und Stolpersteine (#102)
- [Datenbankanbindung und Migrationen](code/datenbank-und-migrationen.md): Pool und Schemaprüfung in `core::db`, `chronos migrate`, Rollen, Exit-Code 75, Tests, Stolpersteine (Healthcheck, Lizenz, rootless Docker)
- [Wireframe-Generator und Prüfung](code/wireframes.md): `wirelib.py`, Story-Skripte, `check.py`; Token in `{…}`, Rahmen als Excalidraw-`frame`, Stolpersteine (`-I`, Raute als Hex), S103-Entscheidung
- [Operationsrahmen (Minimalstand)](code/operationsrahmen.md): `Frame`, `Operation`, `Context`, Geltungsbereich, Probelauf, Test-Principal, Tabellen `person`/`verlauf`/`outbox`, Tests, Stolpersteine, Messwerte

## Lektionen
- [Wissen nur im Wiki](lessons/wissen-nur-im-wiki.md): Kein Agenten-Gedächtnis, alles projektgebunden im Wiki

## Vorschläge an `docs/`
- [Operationsnamen englisch](proposals/2026-11-27-operationsnamen-englisch.md): angenommen und in `docs/` umgesetzt: `area.verb` statt `bereich.verb`
- [Image und Deployment-Form](proposals/2026-11-24-image-und-deployment-widerspruch.md): Kapitel 7 (kustomize) gegen ADR-011 (Helm-Hook); angenommen und in `docs/` umgesetzt: ein Image, Helm statt kustomize
- [Hell/Dunkel nur System](proposals/2026-11-27-hell-dunkel-nur-system.md): K-012 „manuelle Umschaltung offen“ → nur `prefers-color-scheme`, kein Schalter; angenommen und in `docs/` umgesetzt
- [Vitest für Frontend-Unit-Tests](proposals/2026-11-27-vitest-fuer-frontend-unit-tests.md): ADR-009 Ebene 1 um Vitest im Frontend ergänzen; erster Fall Tokentest #106; angenommen und in `docs/` umgesetzt
- [Breakpoints und Textbreite](proposals/2026-11-27-breakpoints-und-textbreite.md): angenommen und in K-012 umgesetzt: `breakpoint.tablet`/`desktop` und `size.text-max`
- [Code-Namen im Glossar](proposals/2026-11-27-code-namen-im-glossar.md): englische Code-Namen für Verlauf, Akteur, Ereignis u. a.; Ticket #101 nannte deutsche Namen (offen)
- [Outbox-Abarbeitung liegt in core](proposals/2026-11-27-outbox-processing-in-core.md): Kapitel 5 nennt sie beim Worker, ADR-009 erlaubt `sqlx` dort nicht (offen)
