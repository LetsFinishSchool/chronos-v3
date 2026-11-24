---
id: F-003
title: Termine
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-001, SH-002]
---

# F-003: Termine

**Story:** Als Leitungsteam-Mitglied möchte ich interne Termine anlegen, ändern und absagen, damit alle im Team informiert sind.

**Umfang:**
- Termin anlegen mit Team, Titel, Beschreibung, Ort, Beginn, Ende
- Terminart: Treffen (mit Rückmeldung) oder Frist/Marke (ohne Rückmeldung, z. B. Anmeldestart, Anmeldeschluss)
- Termin ändern, verschieben, absagen
- optional einer Veranstaltung zuordnen

**Entscheidung:** Mindestteilnehmerzahl und daraus abgeleiteter Terminstatus entfallen gegenüber chronos-root; die Leitung entscheidet anhand der Antwortübersicht ([F-005](F-005-rueckmeldung.md)).

**Serientermine:** siehe [F-014](F-014-serientermine.md).

**Entscheidung:** Jedes Team und jeder Termin hat eine Zeitzone (Standard Europe/Berlin); die Anzeige wird auf die Zeitzone der Person umgerechnet.

**Anforderung mit Akzeptanzkriterien:** [FA-003](../anforderungen/FA-003-termine.md)
