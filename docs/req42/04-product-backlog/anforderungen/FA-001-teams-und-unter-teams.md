---
id: FA-001
title: Teams und Unter-Teams
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-001]
---

# FA-001: Teams und Unter-Teams

**Akzeptanzkriterien:**
1. Ein Mitglied legt ein Team an und ist danach dessen Mitglied.
2. Ein Unter-Team kann in jedem Team oder Unter-Team angelegt werden; Zyklen sind ausgeschlossen.
3. Wer Mitglied eines Unter-Teams ist, ist automatisch Mitglied aller übergeordneten Teams und sieht deren Termine ([M-002](../../05-modelle/M-002-berechtigungen.md)); Gäste über Einladungslink erben nicht nach oben.
4. Der Baum zeigt alle Teams, in denen die Person Mitglied ist, samt Unter-Teams.
5. Jede Änderung an Teams und Mitgliedschaften (anlegen, entfernen, löschen) wird mit Akteur und Zeitpunkt im Änderungsverlauf festgehalten.
6. Beim Löschen eines Teams mit Unter-Teams oder Terminen verlangt das System eine ausdrückliche Bestätigung; Unter-Teams und Termine werden mitgelöscht und sind 30 Tage wiederherstellbar ([FA-017](FA-017-rueckgaengig-machen.md)).

Feature: [F-001](../features/F-001-teams-und-unter-teams.md)
