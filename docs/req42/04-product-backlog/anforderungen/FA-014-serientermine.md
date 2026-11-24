---
id: FA-014
title: Serientermine
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-014]
---

# FA-014: Serientermine

**Akzeptanzkriterien:**
1. Eine Serie lässt sich mit jeder gültigen RRULE nach RFC 5545 anlegen; ungültige Regeln werden mit Fehlermeldung abgelehnt.
2. Ein Team kann Schulferien-Zeiträume hinterlegen; Vorkommen einer Serie, die in einen Ferienzeitraum fallen, entfallen, wenn die Serie diese Ausnahme aktiviert hat.
3. Einzelne Vorkommen lassen sich absagen oder verschieben, ohne die Serie zu ändern.
4. Rückmeldungen gelten je Vorkommen; Änderungen an „ab hier“ oder „ganze Serie“ benachrichtigen die Eingeladenen ([M-004](../../05-modelle/M-004-benachrichtigungsmatrix.md)).
5. Eine gelöschte Serie lässt sich 30 Tage wiederherstellen ([F-017](../features/F-017-rueckgaengig-machen.md)).
6. Der Kalender-Feed enthält die Vorkommen ([F-009](../features/F-009-kalender-feed.md)).

Feature: [F-014](../features/F-014-serientermine.md)
