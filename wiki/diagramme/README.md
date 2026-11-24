# C4-Generator

**Die Diagramme liegen seit 2026-11-24 in `docs/arc42/diagramme/`** (auf Anweisung des Product Owners, Status Entwurf bis zur Freigabe). Hier liegt nur der Generator; `generate.py` schreibt dorthin.

Excalidraw-Diagramme (`.excalidraw`, öffnen mit excalidraw.com oder der IDE-Erweiterung) mit SVG-Vorschau. Sie zeigen den Stand der freigegebenen arc42-Kapitel und ADR-001 bis ADR-013 (Stand 2026-11-24). **Nicht verbindlich**: Es gilt `docs/arc42/`. Ändert sich dort etwas, `generate.py` anpassen und neu erzeugen.

| Datei | C4-Ebene | arc42-Sicht |
|---|---|---|
| `c4-1-systemkontext` | 1 Kontext | Kap. 3 Fachlicher und technischer Kontext |
| `c4-2-container` | 2 Container | Kap. 5 und 7 (Web, Worker, PostgreSQL, SPA, Job) |
| `c4-3-komponenten` | 3 Komponente | Kap. 5 Ebene 1 (Bausteine, Abhängigkeitsrichtungen) |
| `c4-3-komponenten-rahmen` | 3 Komponente | Kap. 5 Ebene 2 (Rahmen der Operationsschicht, ADR-005) |
| `c4-dynamisch-l1-gastlink`, `-l2-termin-aendern`, `-l4-assistent` | Dynamisch | Kap. 6 Laufzeit L-1, L-2, L-4 |
| `c4-deployment` | Deployment | Kap. 7 Verteilung (k3s, prod und staging) |

Nicht gezeichnet: Kap. 4 (Strategie), 8 (Konzepte), 9 bis 12 sind keine Struktursichten; L-3, L-5 bis L-7 sind Textszenarien ohne neue Elemente.

## Neu erzeugen

`python3 generate.py` (nur Standardbibliothek). `c4lib.py` erzeugt aus einem Modell sowohl Excalidraw-JSON (Pfeile und Beschriftungen gebunden, im Editor verschiebbar) als auch SVG. Die Pfeilführung ist automatisch (gerade Linien); nach Handarbeit in Excalidraw die Datei dort speichern und `generate.py` nicht mehr ausführen, sonst geht die Handarbeit verloren.
