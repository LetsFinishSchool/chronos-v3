---
title: Wireframe-Generator und Prüfung
type: code
sources:
  - issue:#114
  - designs/README.md
  - docs/req42/04-product-backlog/ticket-typen.md (DoR Punkt 4)
  - designs/wireframes/generator/wirelib.py
  - designs/wireframes/generator/S103-startseite.py
  - designs/wireframes/generator/check.py
confidence: mittel
last-verified: 2026-11-27
---

# Wireframe-Generator und Prüfung

Wireframes nach DoR Punkt 4 entstehen per Skript in `designs/wireframes/generator/` (nur Standardbibliothek), nicht über `docs/arc42/diagramme/generator/c4lib.py`, denn das ist auf C4 zugeschnitten und liegt in `docs/`.

## Aufbau
- `wirelib.py`: Modell (Rahmen, Rechteck, Linie, Text) erzeugt `.excalidraw` und `.svg`. Liest Farben (heller Modus), Abstände und Schriftstile aus `designs/tokens/tokens.json`, damit Füllung und Beschriftung nicht auseinanderlaufen.
- `S<Nr>-<kurzname>.py`: Modell einer Story, ist die Quelle. Nach Handarbeit im Excalidraw-Editor nicht mehr ausführen.
- `check.py`: prüft alle `designs/wireframes/*.excalidraw` (oder übergebene Dateien): JSON, eindeutige IDs, Verweise (`frameId`, `containerId`, `boundElements`, Pfeilbindungen), drei Rahmen `Mobil 320 px`, `Tablet 768 px`, `Desktop 1280 px` mit passender Breite, in jedem Rahmen die fünf Zustandsnamen (Normal, Laden, Fehler, Leer, Ohne Berechtigung) als Text, kein Hex-Wert in Texten oder Rahmennamen, jedes `{token}` existiert, SVG daneben vorhanden.

## Konventionen
- Rahmen sind Excalidraw-Elemente vom Typ `frame`, die Beschriftung steht in `name`; Kinder tragen `frameId`.
- Token-Namen stehen in Beschriftungen in geschweiften Klammern (`{bg.page}`, `{space.4}`, `{typography.style.heading-h1}`), so trennt die Prüfung sie von Fluent-Schlüsseln (`start.title`). Semantische Farben ohne Modus (`bg.page`, nicht `semantic.light.bg.page`), alles andere mit vollem Pfad.
- Ticketnummern in Beschriftungen als „Ticket 103“, nicht mit Raute: `#103` sieht für die Hex-Prüfung wie eine Farbe aus.
- Nicht zutreffende Zustände stehen als Text „Leer: nicht zutreffend …“ im Rahmen.

## Stolpersteine
- `python3 -I` nimmt das Skriptverzeichnis nicht in `sys.path` auf; die Skripte fügen es selbst ein, sonst schlägt `import wirelib` fehl.
- Textbreiten sind geschätzt (Zeichenzahl mal Faktor). Unterstreichungen und Umbrüche weichen im Editor leicht ab.
- Excalidraw kennt keine fette Schrift; der Schriftstil steht nur in der Beschriftung, die SVG zeigt ihn.
- Die Excalidraw-Datei aus #114 wurde nicht im Editor geöffnet; geprüft sind `check.py` und die SVG-Vorschau.

## S103 Startseite (#114)
Variante „schlicht“ vom Product Owner gewählt (Textspalte oben links, keine Karte, keine Kopfzeile), weil sie ohne neue Komponente auskommt und #103 nicht blockiert. Ladezustand nur als Statustext. Die zunächst fehlenden Tokens hat der PO in derselben Session festgelegt und in diesem PR eintragen lassen (Abweichung von „Nicht Teil: neue Tokens“): `breakpoint.tablet` 768, `breakpoint.desktop` 1280, `size.text-max` 576 px (gestrichelte Linie). Die Rahmenbreiten von Tablet und Desktop liest das Skript aus diesen Tokens. Offen bleibt: Texte der Ladehülle stehen statisch in `index.html` (Spannung zu V-3, Hinweis an #103).
