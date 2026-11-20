---
title: K-007 Mehrsprachigkeit und Zeitzonen
status: entwurf
quellen: [req42 RB-001, FA-003, RA-008]
---

# K-007: Mehrsprachigkeit und Zeitzonen

**Mehrsprachigkeit** ([RB-001](../../req42/07-randbedingungen/RB-001-mehrsprachigkeit.md)):

- Oberfläche **und** Benachrichtigungen (Push, E-Mail, Messenger) sowie Assistent-Antworten: Deutsch und Englisch, weitere Sprachen ohne Umbau.
- Sprache je Person einstellbar; Gäste: Browsersprache, Rückfall Deutsch.
- Texte stehen nicht verstreut im Code; Benachrichtigungstexte werden **je Empfänger** in dessen Sprache erzeugt, nicht beim Auslöser.
- Fachbegriffe folgen dem [Glossar](../../req42/08-terminologie/glossar.md).

**Zeitzonen** ([FA-003](../../req42/04-product-backlog/anforderungen/FA-003-termine.md)):

- Beginn, Ende und Erinnerungen gelten in der Zeitzone des Termins (Standard: Team, Europe/Berlin).
- Anzeige in der Zeitzone der Person; Sommerzeitwechsel sind zu berücksichtigen, insbesondere bei Serien (RRULE in Terminzeitzone).
- Zeitpunkte werden eindeutig gespeichert; Umrechnung erst bei der Anzeige.

**Entschieden (PO 2026-11-20):** Zeitpunkt in UTC plus Zeitzone des Termins (Serien bleiben über die Sommerzeit lokal stabil, RFC 5545 TZID). Risiko: veraltete Zeitzonendatenbank, regelmäßig aktualisieren.

**Entschieden (PO 2026-11-20):** Übersetzungen als Textdateien je Sprache im Repository (JSON oder PO, konkretes Format mit E-004/E-002).

**Offen (nach E-002, PO 2026-11-20):** Plural-/Datumsformate.
