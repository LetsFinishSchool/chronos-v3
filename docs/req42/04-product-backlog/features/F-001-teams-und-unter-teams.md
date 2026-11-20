---
id: F-001
title: Teams und Unter-Teams
status: entwurf
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-003, SH-002]
---

# F-001: Teams und Unter-Teams

**Story:** Als Leitungsteam-Mitglied möchte ich Teams und beliebig tief verschachtelte Unter-Teams anlegen, damit die Struktur meines Verbands abgebildet ist.

**Umfang:**
- Team anlegen, umbenennen, löschen
- Unter-Team in einem Team oder Unter-Team anlegen, beliebige Tiefe
- Team-Baum anzeigen

**Entscheidung:** Mitgliedschaft wird **nach oben vererbt**: Wer Mitglied eines Unter-Teams ist, ist auch Mitglied aller übergeordneten Teams. Ausnahme: Gäste über Einladungslink sind nur Mitglied des konkreten Teams, für das sie eingeladen wurden.

**Entscheidung:** Löschen eines Teams löscht Unter-Teams und Termine mit (Kaskade); alles ist über „Rückgängig“ wiederherstellbar ([F-017](F-017-rueckgaengig-machen.md)).

**Anforderung mit Akzeptanzkriterien:** [FA-001](../anforderungen/FA-001-teams-und-unter-teams.md)
