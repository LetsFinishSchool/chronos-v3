---
title: C4-Diagramme zu arc42
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
---

# C4-Diagramme

Excalidraw-Diagramme (`.excalidraw`, öffnen mit excalidraw.com oder der IDE-Erweiterung) mit SVG-Vorschau. Sie veranschaulichen die freigegebenen Kapitel und ADR-001 bis ADR-013 (Stand 2026-11-24), enthalten aber keine eigenen Entscheidungen. Bei Abweichung gilt der Text der Kapitel.

| Diagramm | C4-Ebene | Kapitel |
|---|---|---|
| [Systemkontext](c4-1-systemkontext.svg) | 1 Kontext | [3 Kontext](../03-kontext/01-fachlicher-kontext.md) |
| [Container](c4-2-container.svg) | 2 Container | [5](../05-bausteine/01-bausteinsicht.md), [7](../07-verteilung/01-verteilungssicht.md) |
| [Bausteine](c4-3-komponenten.svg) | 3 Komponente | [5, Ebene 1](../05-bausteine/01-bausteinsicht.md) |
| [Rahmen der Operationsschicht](c4-3-komponenten-rahmen.svg) | 3 Komponente | [5, Ebene 2](../05-bausteine/01-bausteinsicht.md), [ADR-005](../09-entscheidungen/ADR-005-operationsschicht.md) |
| [L-1 Gastlink](c4-dynamisch-l1-gastlink.svg), [L-2 Termin ändern](c4-dynamisch-l2-termin-aendern.svg), [L-4 Assistent](c4-dynamisch-l4-assistent.svg) | Dynamisch | [6 Laufzeit](../06-laufzeit/01-laufzeitszenarien.md) |
| [Deployment](c4-deployment.svg) | Deployment | [7 Verteilung](../07-verteilung/01-verteilungssicht.md) |

Offen und gestrichelt gezeichnet: Backup (E-010), Ferien-Abruf, Messenger, Datenübernahme (E-017). Die Komponentendiagramme zeigen Bausteine, nicht Crates; der Crate-Zuschnitt (ADR-009) steht in Kapitel 5, Crate-Zuschnitt.

Erzeugt aus `generator/generate.py`. Wer in Excalidraw von Hand nachbessert, führt den Generator nicht mehr aus.
