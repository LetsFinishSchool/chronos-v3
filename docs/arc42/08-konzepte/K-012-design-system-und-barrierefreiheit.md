---
title: K-012 Design-System und Barrierefreiheit
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 QA-005, RB-011, DoD in ticket-typen.md, ADR-007, ADR-009, ADR-010]
---

# K-012: Design-System und Barrierefreiheit

**Ziel:** Jede Oberfläche sieht gleich aus, erfüllt WCAG 2.2 Stufe AA und ist ab 320 px Breite bedienbar ([QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md)). Farben, Abstände und Schriften werden nirgends neu festgelegt, sondern kommen aus Tokens.

## 1. Tokens
- Quelle der Werte: `designs/tokens/tokens.json` (W3C-Design-Token-Format). Die Datei wird von Hand gepflegt; Änderungen gehen durch den Kontrasttest (Abschnitt 3).
- Zwei Ebenen: **Primitives** (Farbskalen) und **semantische Tokens** je Modus `light` und `dark` (`bg.*`, `text.*`, `border.*`, `brand.*`, `status.*`, `focus.ring`). Komponenten und Wireframes verwenden nur semantische Tokens, nie Primitives oder Hex-Werte.
- Weitere Tokens: Abstände (`space.*`, 4-px-Raster), Radien, Typografie (Inter), Schatten, Verläufe, Layoutmaße (`size.text-max` = 576 px, höchste Breite einer Lesespalte, etwa 72 Zeichen).
- Layoutstufen: Mobil ist die Basis ab 320 px; `breakpoint.tablet` (768 px) und `breakpoint.desktop` (1280 px) sind Untergrenzen (`min-width`). Sie entsprechen den drei Rahmen der Wireframes (Definition of Ready, Punkt 4) und sind Referenzwerte für Media Queries, keine CSS-Variablen.
- Im Frontend ([ADR-007](../09-entscheidungen/ADR-007-frontend-spa-svelte.md)) werden die Tokens als CSS-Variablen bereitgestellt; der Modus folgt nur dem System (`prefers-color-scheme`), ohne Schalter und ohne gespeicherte Wahl (**entschieden, PO 2026-11-27**). Ein Schalter wäre eine eigene Story.

## 2. Regeln für Farbe und Bedienelemente
1. **Kontrast:** Text mindestens 4,5 : 1 (SC 1.4.3), Bedienelemente und aussagekräftige Grafiken mindestens 3 : 1 (SC 1.4.11), in beiden Modi.
2. **Farbe nie allein:** Zusage, Absage, Ausstehend, Fehler und Warnung tragen zusätzlich Symbol oder Text (SC 1.4.1). Im Dunkelmodus unterscheiden sich die getönten Flächen nicht von `bg.surface`.
3. **Rahmen:** `border.default` ist rein dekorativ. Eingabefelder, Checkbox, Radio, Schalter und Auswahlkacheln nutzen `border.control` (mindestens 3 : 1).
4. **Fokus:** sichtbarer Fokusrahmen in `focus.ring`, mindestens 2 px, nie verdeckt (SC 2.4.11).
5. **Verläufe:** Text auf Verläufen nur, wenn jeder Punkt des Verlaufs 4,5 : 1 gegen die Textfarbe erreicht; sonst Text auf Volltonfläche oder Karte.
6. **Zielgröße:** Bedienelemente mindestens 24 × 24 px oder mit ausreichendem Abstand (SC 2.5.8).
7. **Dunkle Primärfläche:** `brand.primary` im Dunkelmodus ist nicht auf `bg.muted` einzusetzen (unter 3 : 1).

## 3. Prüfung
- **Tokentest** (CI): liest `tokens.json`, löst Aliase auf und prüft alle Text-Hintergrund-Paare (4,5 : 1), Rahmen, Marke, Status und Fokus gegen `bg.surface` und `bg.page` (3 : 1) und alle Verlaufspunkte, beide Modi. Scheitert bei jeder Unterschreitung.
- **axe-core** in den Oberflächentests ([ADR-009](../09-entscheidungen/ADR-009-teststrategie-und-architekturregeln.md), Ebene 6) deckt Verläufe und Nicht-Text-Kontraste nicht zuverlässig ab; der Tokentest schließt diese Lücke.
- **Manuell je Feature:** Durchlauf mit Tastatur und Screenreader ([DoD](../../req42/04-product-backlog/ticket-typen.md)).

## 4. Entwurf neuer Oberflächen
Jede Story mit sichtbarer UI hat einen Wireframe für 320, 768 und 1280 px (Excalidraw, `designs/wireframes/`), der nur Token-Namen und vorhandene Komponenten nennt (Definition of Ready). Fehlt ein Token oder eine Komponente, wird dies zuerst als Design-System-Task umgesetzt.

## Risiken
- Knappe Werte: dunkle Statusflächen 3,01 bis 3,13 : 1 auf `bg.surface`; jede Änderung der Grauwerte erneut prüfen (der Tokentest tut das).
- Das Aussehen im Dunkelmodus (hellere Primärfläche mit dunkler Schrift) ist eine Gestaltungsentscheidung des Product Owners (getroffen 2026-11-24).
