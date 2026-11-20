---
id: FA-015
title: KI-Assistent
status: entwurf
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-015]
---

# FA-015: KI-Assistent

**Akzeptanzkriterien:**
1. Der Assistent kann jede Funktion ausführen, die Chronos anbietet; die Weboberfläche muss das nicht können.
2. Vor **jeder** Schreiboperation zeigt der Assistent, was er tun würde (betroffene Objekte, Änderungen, Anzahl), und führt sie erst nach ausdrücklicher Freigabe aus; ohne Freigabe wird nichts geschrieben.
3. Lesende Operationen brauchen keine Freigabe.
4. Der Assistent handelt nur mit den Rechten der angemeldeten Person ([M-002](../../05-modelle/M-002-berechtigungen.md)).
5. Alle vom Assistenten ausgeführten Änderungen stehen im Änderungsverlauf als „durch Assistent im Auftrag von …“ ; gelöschte Objekte sind wiederherstellbar ([F-017](../features/F-017-rueckgaengig-machen.md)).
6. Jede KI-Nutzung wird der Person (ersatzweise dem Team) mit Einzelposten zugeordnet ([RB-010](../../07-randbedingungen/RB-010-kostenzuordnung.md)).
7. Der Assistent antwortet in der Sprache der Person ([RB-001](../../07-randbedingungen/RB-001-mehrsprachigkeit.md)).

Feature: [F-015](../features/F-015-ki-assistent.md)
