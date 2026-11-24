---
title: C4-Diagramme zu arc42
type: concept
sources:
  - docs/arc42/diagramme/README.md
  - docs/arc42/03-kontext/
  - docs/arc42/05-bausteine/01-bausteinsicht.md
  - docs/arc42/06-laufzeit/01-laufzeitszenarien.md
  - docs/arc42/07-verteilung/01-verteilungssicht.md
  - docs/arc42/09-entscheidungen/ADR-002-zerlegung-monolith-plus-worker.md
  - docs/arc42/09-entscheidungen/ADR-005-operationsschicht.md
  - docs/arc42/09-entscheidungen/ADR-008-sitzung-und-gast-identitaet.md
confidence: mittel
last-verified: 2026-11-24
---

# C4-Diagramme zu arc42

Acht Excalidraw-Diagramme in `docs/arc42/diagramme/` (vom PO freigegeben); Generator in `docs/arc42/diagramme/generator/`. Zuordnung C4 zu arc42: Kontext = Kap. 3, Container = Kap. 5/7, Komponente = Kap. 5, Dynamisch = Kap. 6, Deployment = Kap. 7.

## Entscheidungen, die sich im Bild niederschlagen
- Zwei Prozesse (Web, Worker), eine Codebasis, eine PostgreSQL-Instanz je Umgebung; Migrationsjob als Helm-Hook (ADR-002, 003, 011).
- KI nur über Gateway (LiteLLM, EU), Assistent und KI-Adapter im Web-Prozess (ADR-006).
- Sitzung als BFF; der Heartbeat läuft im Worker, Back-Channel-Logout trifft den Web-Prozess (ADR-008).
- Der Rahmen der Operationsschicht trägt Transaktion, Berechtigung, Verlauf, Outbox, Vorschau (ADR-005).

## Lücken und Annahmen der Zeichnung
- Crate-Zuschnitt (ADR-009) ist offen; die Komponenten folgen den Bausteinen aus Kap. 5, nicht den Spike-Crates.
- Offen und gestrichelt bzw. ohne Prozesszuordnung: Backup (E-010), Ferien-Abruf, Messenger, Datenübernahme (E-017).
- Der Pfeil Kanäle nach Kostenerfassung (Posten für E-Mail/Messenger) und KI-Adapter nach Kostenerfassung folgt Kap. 5 Regel 4; die Kostenerfassung liegt dort im Querschnitt des Web-Prozesses, die Posten entstehen auch im Worker (über die Datenbank).
- Die Excalidraw-Dateien wurden nicht im Editor geöffnet; geprüft sind JSON-Konsistenz (Bindungen) und die SVG-Vorschau aus demselben Modell.
