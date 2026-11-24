---
id: FA-016
title: Dauerhafte Zeitraumsregeln (Bulk)
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-016]
---

# FA-016: Dauerhafte Zeitraumsregeln (Bulk)

**Akzeptanzkriterien:**
1. Beim Anlegen der Regel werden alle bestehenden Termine im Zeitraum abgesagt (nach Vorschau und Freigabe, wenn über den Assistenten).
2. Ein später im Zeitraum angelegter Termin wird automatisch abgesagt und die Person bekommt einen Hinweis, welche Regel gewirkt hat.
3. Wird die Regel aufgehoben, sind die durch sie abgesagten Termine wieder geplant; manuell abgesagte bleiben abgesagt.
4. Absagen durch Regeln lösen die üblichen Benachrichtigungen aus, gebündelt statt je Termin.
5. Anlegen und Aufheben stehen im Änderungsverlauf ([F-017](../features/F-017-rueckgaengig-machen.md)).

Feature: [F-016](../features/F-016-zeitraumsregeln.md)
