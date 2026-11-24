# Wiki-Index

Agenten: zuerst hier lesen. Eine Zeile pro Seite, nach Typ gruppiert. Pflichtpflege bei jedem Ingest.

## Konzepte
- [E-002 Spike: Lehren](concepts/e-002-spike-ergebnisse.md): Lehren für künftige Agentenläufe (Ergebnisse in ADR-004)
- [C4-Diagramme zu arc42](concepts/c4-diagramme-arc42.md): Excalidraw-Diagramme (Kontext, Container, Komponenten, Laufzeit, Verteilung) in `docs/arc42/diagramme/` (Generator in `docs/arc42/diagramme/generator/`), Lücken der Zeichnung
- [Farb- und Token-System](concepts/farb-und-token-system.md): Purple-Schema, Textstile, Schatten, Verläufe; WCAG-AA-Anpassungen und Prüfstand; Datei `designs/tokens/tokens.json` (kein Figma-Export im Repo)
- [Worktrees: .env und .envrc übernehmen](concepts/worktree-dateien-uebernehmen.md): herdr kopiert keine gitignorierten Dateien; Hook `.githooks/post-checkout` liest `.worktreekeep`
- [req42-Backlog und GitHub-Issues](concepts/req42-anforderung-vs-feature-und-tickets.md): FA/F-Unterschied, Überführung in 91 Issues, Anpassungen, Stolpersteine
- [Crate-Zuschnitt (Diagramm)](diagramme/crate-zuschnitt.excalidraw): sieben Crates mit erlaubten und verbotenen Kanten zu `docs/arc42/05-bausteine/02-crate-zuschnitt.md` (Excalidraw, SVG-Vorschau, Skript `crate-zuschnitt.py`)

## Code
- [Cargo-Workspace und Architekturtest](code/cargo-workspace.md): Aufbau des Workspace, Binary `chronos`, Architekturtest mit Positivliste, Stolperstellen (Exit-Code 2 gehört clap, eigener Code 69; Zyklen über Dev-Abhängigkeiten; ungenutzte Abhängigkeiten ab Cargo 1.100), Prüfbefehle

## Lektionen
- [Wissen nur im Wiki](lessons/wissen-nur-im-wiki.md): Kein Agenten-Gedächtnis, alles projektgebunden im Wiki

## Vorschläge an `docs/`
- [Image und Deployment-Form](proposals/2026-11-24-image-und-deployment-widerspruch.md): Kapitel 7 (kustomize) gegen ADR-011 (Helm-Hook); „ein Image“ ist entschieden, blockiert #104 (offen)
