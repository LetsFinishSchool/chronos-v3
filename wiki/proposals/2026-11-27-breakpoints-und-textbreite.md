---
title: Breakpoints und maximale Textbreite in K-012
datum: 2026-11-27
betrifft: docs/arc42/08-konzepte/K-012-design-system-und-barrierefreiheit.md
art: änderung
status: angenommen
---

## Beobachtung
Für das Wireframe S103 (#114) fehlten Tokens für die Layoutstufen 768 und 1280 px und für die maximale Breite einer Textspalte. Die bisherigen `breakpoint.mobile-design` (390) und `breakpoint.desktop-design` (1440) waren nur die Entwurfsbreiten der alten Figma-Screens. Der Product Owner hat am 2026-11-27 in der Session zu #114 entschieden; `designs/tokens/tokens.json` ist angepasst. K-012 Abschnitt 1 zählt unter „Weitere Tokens“ weder Breakpoints noch Layoutmaße auf. #120 gibt `breakpoint.*` bewusst nicht als CSS-Variable aus (in Media Queries nicht nutzbar).

## Vorschlag
In K-012 Abschnitt 1 die Zeile „Weitere Tokens“ ersetzen durch:

> - Weitere Tokens: Abstände (`space.*`, 4-px-Raster), Radien, Typografie (Inter), Schatten, Verläufe, Layoutmaße (`size.text-max` = 576 px, höchste Breite einer Lesespalte, etwa 72 Zeichen).
> - Layoutstufen: Mobil ist die Basis ab 320 px; `breakpoint.tablet` (768 px) und `breakpoint.desktop` (1280 px) sind Untergrenzen (`min-width`). Sie entsprechen den drei Rahmen der Wireframes (DoR Punkt 4) und sind Referenzwerte für Media Queries, keine CSS-Variablen.

## Wirkung
- Wireframes nennen die Stufen über Token-Namen; `check.py` prüft sie.
- #103 und #120 schreiben Media Queries mit diesen Werten (die Werte stehen im Code, da `var()` in Media Queries nicht geht).
- Kein Einfluss auf den Kontrasttest #106.

## Entscheidung (Mensch)
Angenommen vom Product Owner am 2026-11-27 (Session zu #114) und in K-012 Abschnitt 1 umgesetzt.
