---
title: K-007 Mehrsprachigkeit und Zeitzonen
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 RB-001, FA-003, RA-008]
---

# K-007: Mehrsprachigkeit und Zeitzonen

**Mehrsprachigkeit** ([RB-001](../../req42/07-randbedingungen/RB-001-mehrsprachigkeit.md)):

- Oberfläche **und** Benachrichtigungen (Push, E-Mail, Messenger) sowie Assistent-Antworten: Deutsch und Englisch, weitere Sprachen ohne Umbau.
- Sprache je Person einstellbar; Gäste: Browsersprache, Rückfall Deutsch.
- Texte stehen nicht verstreut im Code; Benachrichtigungstexte werden **je Empfänger** in dessen Sprache erzeugt, nicht beim Auslöser.
- Fachbegriffe folgen dem [Glossar](../../req42/08-terminologie/glossar.md).

**Zeitzonen** ([FA-003](https://github.com/LetsFinishSchool/chronos-v3/issues/13)):

- Beginn, Ende und Erinnerungen gelten in der Zeitzone des Termins (Standard: Team, Europe/Berlin).
- Anzeige in der Zeitzone der Person; Sommerzeitwechsel sind zu berücksichtigen, insbesondere bei Serien (RRULE in Terminzeitzone).
- Zeitpunkte werden eindeutig gespeichert; Umrechnung erst bei der Anzeige.

**Entschieden (PO 2026-11-20):** Zeitpunkt in UTC plus Zeitzone des Termins (Serien bleiben über die Sommerzeit lokal stabil, RFC 5545 TZID). Risiko: veraltete Zeitzonendatenbank, regelmäßig aktualisieren. Zeitbibliothek ([ADR-012](../09-entscheidungen/ADR-012-zeitbibliothek.md)): `jiff` im Fachkern mit eingebetteter Zeitzonendatenbank, `chrono` nur an den Rändern (`rrule`, `sqlx`).

**Entschieden (PO 2026-11-20, Format geändert 2026-11-24):** Übersetzungen als Textdateien je Sprache im Repository. Das Format ist **Fluent (`.ftl`)** in Server und Client ([ADR-010](../09-entscheidungen/ADR-010-uebersetzungen-fluent.md), freigegeben 2026-11-24). Die frühere Vorgabe „JSON oder PO“ entfällt; sie war keine Anforderung des Product Owners.

**Entschieden (PO 2026-11-24, ADR-010):** Datums- und Zahlenformate: Browser über `Intl`, Server formatiert vor der Übergabe an Fluent (ICU4X mit `jiff`, falls nötig). Plural und Geschlecht stehen in den Fluent-Nachrichten.
