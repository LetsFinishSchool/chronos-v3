---
title: Farb- und Token-System (aus Figma-Export)
sources: [designs/tokens/tokens.json, designs/README.md, docs/req42/04-product-backlog/ticket-typen.md (WCAG 2.2 AA), wiki/proposals/2026-11-24-farbschema-wcag-aa.md]
confidence: medium
last-verified: 2026-11-27
---

# Farb- und Token-System

> Entscheidung des Nutzers: Kein Figma-Export im Repo. `designs/tokens/tokens.json` ist die von Hand gepflegte Quelle; die Werte wurden aus dem bisherigen Figma-Design übernommen (Variablen-Export und Figma-Datei per MCP, 2026-11-24). Wer die Werte nachprüfen will, braucht Zugriff auf die Figma-Datei „Chronos – App Screens (reduced Color Set)“.

Die Werte stammen aus dem Figma-Variablen-Export des bisherigen Designs (vom Product Owner bereitgestellt). Die früheren Werte aus chronos-root (Indigo/PrimeVue) sind **verworfen**: Das Design nutzt Purple, nicht Indigo.

## Inhalt des Exports
- **Primitives** (Figma-Collection, nicht veröffentlicht): `white`, `gray` (Tailwind-gray: 50–700, 900), `neutral` (700/800/900, nur Dunkel), `purple` (50, 300, 400, 500, 600, 900), `green` (50, 500, 600, 700), `red` (50, 400, 500, 600, 700, 900), `yellow` (50, 500), `amber` (700). Nur die tatsächlich genutzten Stufen.
- **Color**, Modi Light und Dark, gleiche 23 Namen, jeweils mit Verwendungsbeschreibung und Figma-Scope: `bg.{page, surface, muted, brand-subtle, success-subtle, danger-subtle, warning-subtle}`, `border.{default, brand, success, danger, control}`, `text.{primary, secondary, muted, brand, on-brand, success, danger}`, `brand.primary`, `status.{success, danger, warning}`.
- **Spacing & Radius**: `space.0,1,2,3,4,5,6,8,10,12,16,20` = 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80 px (4-px-Raster); `radius.md` 8, `radius.lg` 12, `radius.full` 9999 px.
- **Layout** (nicht aus Figma, PO-Entscheidung 2026-11-27 in #114): `breakpoint.tablet` 768 und `breakpoint.desktop` 1280 px als `min-width`-Untergrenzen, Mobil ist die Basis ab 320 px; ersetzen `breakpoint.mobile-design` (390) und `desktop-design` (1440), die nur Entwurfsbreiten der alten Screens waren. `size.text-max` 576 px (36 rem, etwa 72 Zeichen in Body M). Freigegeben in `docs/arc42/08-konzepte/K-012-design-system-und-barrierefreiheit.md` Abschnitt 1 (Vorschlag [Breakpoints und Textbreite](../proposals/2026-11-27-breakpoints-und-textbreite.md) angenommen).

Die Beschreibungen belegen die Fachsprache des Designs: success = Zusagen/Zugesagt, danger = Absagen/Fehler, warning = Ausstehend, brand-subtle = ausgewählt/Info; `border.control` verlangt ausdrücklich ≥ 3 : 1 (WCAG 1.4.11).

## Kontrastmessung der Figma-Werte (WCAG-Formel, einmalig berechnet)
- Gepaarte Text-Hintergründe (z. B. `text.success` auf `bg.success-subtle`, kleinster Wert hell 4,79) bestehen. Vollständige Matrix (jeder Text-Token auf jedem `bg.*`): nur dunkel `text.danger` auf `bg.muted` (3,75) und `bg.brand-subtle` (3,93) fällt durch.
- `border.control` 4,8 (hell) und 6,0 (dunkel): erfüllt 3 : 1.
- **Lücke Dunkelmodus:** `brand.primary` und `status.*` sind in Dark identisch zu Light (purple 600, green 700, red 600, amber 700). Auf `bg.surface` (neutral 800) messen die `status.*` 3,01 bis 3,13 : 1 (knapp bestanden); `brand.primary` 2,81 liegt unter 3 : 1. Gilt nur, wo die Fläche ihre Grenze allein durch den Farbunterschied zeigt (Buttons mit Text sind unkritisch, Text darauf hat 5,38).
- **Dunkel: `bg.success-subtle`, `bg.danger-subtle`, `bg.warning-subtle` = neutral 800 = `bg.surface`.** Im Dunkelmodus gibt es keine Tönung für Zusage/Absage/Ausstehend; die Unterscheidung läuft nur über Text- und Rahmenfarbe. Farbe darf nie allein tragen (WCAG 1.4.1): Symbol oder Text ergänzen.
- `border.default` 1,2 (hell) / 1,7 (dunkel): nur dekorativ zulässig.
- Der Warnton mischt `yellow` (Fläche) und `amber` (Status) ohne `text.warning`/`border.warning`.

## Ergänzung aus der Figma-Datei (per MCP gelesen, in `tokens.json` eingetragen)
- **Typografie:** Inter, neun Stile: Display 48/55 bold; H1 30/38 bold; H2 24/32 bold; H3 18/27 semibold; Body M 16/24 regular und semibold; Body S 14/20 regular und semibold; Caption 12/16 regular; Zeichenabstand 0.
- **Schatten:** sm, md, lg (je zwei Ebenen, Farbe #0000001A, Werte wie Tailwind shadow-sm/md/lg).
- **Verläufe:** Brand (purple 600 nach pink 500, Primär-Buttons, FAB, Logoschrift), Landing (purple 600, pink 500, orange 400, Hintergrund der Public-Seiten); Overlay Weiß 20 %. Pink und Orange stehen nicht im Variablen-Export, die Hex-Werte (#EC4899, #FB923C) sind die Tailwind-Standardwerte aus den Namen und noch zu bestätigen.
- **Symbole:** 78 Lucide-Icons à 24 px. **Komponenten und Screens** (nicht im Repo): Das Design enthält Button-, Formular-, Karten-, Dialog- und Listenkomponenten sowie Screens für Public (Landing, Onboarding, Installation, Impressum, Datenschutz), App (Agenda, Termin-Detail, Freunde, Gruppen, Profil, Einstellungen, Umfrage), Dialoge und Admin. Screens sind nur mobil (390 px) gestaltet, die Landing-Seite zusätzlich 1440 px.

## Funde aus der Figma-Datei
- **Verläufe und Kontrast:** Weiße Schrift auf dem Brand-Verlauf hat am Ende (pink 500) nur 3,53 : 1, auf Orange (Landing) 2,26 : 1. Primärbuttons mit Verlauf und Text darauf verfehlen AA, solange der Text bis ins rosa Ende reicht. Nicht geprüft, wo Text auf dem Landing-Verlauf steht (er steht auf Glass Cards).
- **Verläufe im Dunkelmodus:** Sie schalten nicht um (Foundations: „alle Flächen außer den Verläufen“).
- **Button-Höhen uneinheitlich:** Primary und Ghost md 44, lg 59 px; Outline, Success, Danger und Secondary md 48, lg 63 px.
- **Checkbox und Radio sind 16 px.** WCAG 2.2 (2.5.8) verlangt mindestens 24 px Zielgröße oder Abstand; ob die klickbare Fläche größer ist, ist im Design nicht erkennbar.
- **Breite:** Nichts ist bei 320 px gestaltet (QA-005 verlangt ab 320 px) und nichts für Desktop außer der Landing-Seite.
- **Keine Screens** für Funktionen des Neuanfangs (Terminfindung, Serien, Zeitraumsregeln, Kosten, Assistent, Labels, Unter-Teams, Verlauf/Rückgängig, Terminnachrichten ist nur als Dialog vorhanden). Die Screens beschreiben das Altsystem.
- Info-/Neutral-Badges und Alert-Tonen `Info` und `Amber` haben keine eigenen Farb-Tokens (`reduced Color Set`).

## Was weiterhin fehlt
Zustände und Maße der einzelnen Komponenten als Werte (nur als Figma-Komponente; über Figma-MCP je Komponente abrufbar), Fokus-Darstellung als Token (Input hat eine Focus-Variante), Bewegung, `info`-/`warning`-Text- und Rahmen-Tokens, Rollenfarben als Tokens (Role Tile existiert). Nicht freigegeben; Aufnahme in `docs/` nur über Vorschlag.

## Anpassungen für WCAG 2.2 AA (vom Product Owner angenommen, in `tokens.json` umgesetzt)
Ausgangsfunde (Messung der Figma-Werte): dunkel `text.danger` auf `bg.muted` 3,75 und `bg.brand-subtle` 3,93; dunkel `brand.primary` auf `bg.surface` 2,81; Brand-Verlauf mit weißer Schrift 3,53; Landing-Verlauf 2,26.

Umgesetzt:
- Dunkel `text.danger` = red 300 `#FCA5A5`; dunkel `brand.primary` = purple 500 `#A855F7` mit `text.on-brand` = neutral 900 (4,53 : 1); Hell bleibt purple 600 mit Weiß (5,38).
- Verlauf Brand: purple 600 nach pink 700 `#BE185D` (min. 5,38 mit Weiß); Landing: purple 600, pink 700, orange 700 `#C2410C` (min. 5,18).
- Neue Tokens: `text.warning` (amber 700 hell, amber 400 dunkel), `text.info` (blue 700 hell, blue 300 dunkel), `focus.ring` (purple 600 hell, purple 400 dunkel; mindestens 2 px, nie verdeckt).
- Prüfung der neuen Datei: 160 Paare (Text 4,5 : 1; Rahmen, Marke, Status, Fokus 3 : 1; Verläufe) in beiden Modi ohne Verstoß; einmalig per Skript, nicht in CI. Knappste Stellen: dunkel `status.*` auf `bg.surface` 3,01 bis 3,13; dunkel `brand.primary` auf `bg.muted` 2,62 (dort nicht als Fläche einsetzen).

Regeln (jetzt in K-012): `border.default` nur dekorativ; Farbe nie allein als Information (Symbol oder Text dazu); Text auf Verläufen nur, wenn alle Stopps 4,5 : 1 erreichen; Checkbox und Radio mindestens 24 px Zielgröße (SC 2.5.8, im bisherigen Design 16 px). Tokentest: Task #106 unter Feature #105 (Design-System, Teil von Epic #1), noch nicht `ready-for-agent` (wartet auf #103). Die Regeln stehen freigegeben in `docs/arc42/08-konzepte/K-012-design-system-und-barrierefreiheit.md` (2026-11-24).
