---
id: F-014
title: Serientermine
status: entwurf
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-001, SH-002]
---

# F-014: Serientermine

**Story:** Als Leitungsteam-Mitglied möchte ich wiederkehrende Termine mit beliebig komplexen Regeln anlegen, damit ich nicht jeden Termin einzeln pflege.

**Umfang:**
- Serien mit den vollen RRULE-Regeln (RFC 5545: Frequenz, Intervall, BYDAY, BYMONTH, BYSETPOS, COUNT, UNTIL usw.)
- Einzelne Vorkommen ausnehmen, verschieben oder absagen
- Ausnahmen für Schulferien (Ferienzeiträume, in denen Vorkommen entfallen)
- Änderung an einem Vorkommen, ab einem Vorkommen oder an der ganzen Serie

**Entscheidung:**
- Schulferien kommen aus einer öffentlichen API (z. B. OpenHolidays) mit lokalem Cache; Zuordnung über das Bundesland des Teams.
- Serien bleiben über die Sommerzeit auf der Wanduhrzeit der Termin-Zeitzone (RRULE mit TZID).

**Anforderung mit Akzeptanzkriterien:** [FA-014](../anforderungen/FA-014-serientermine.md)
