---
id: FA-002
title: Mitglieder und Einladungslink
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-002]
---

# FA-002: Mitglieder und Einladungslink

**Akzeptanzkriterien:**
1. Ein Mitglied erzeugt einen Einladungslink für einen Termin; er enthält ein nicht erratbares Token ([QA-007](../../06-qualitaet/QA-007-sicherheit-und-datenschutz.md)).
2. Wer den Link öffnet, gibt einen Namen an und antwortet, ohne Konto.
3. Ein widerrufener Link liefert keine Daten und erlaubt keine Antwort.
4. Der Beitritt zu einem Team über einen Link ist möglich, setzt aber ein Konto voraus und ist nicht zwingend für die Antwort.
5. Jedes Mitglied kann Mitglieder entfernen und ein Team verlassen; die Aktion wird im Änderungsverlauf festgehalten und die Betroffenen werden benachrichtigt ([M-004](../../05-modelle/M-004-benachrichtigungsmatrix.md)).
6. Ein Gast über Link ist nur Mitglied des konkreten Teams, nicht der übergeordneten.

Feature: [F-002](../features/F-002-mitglieder-und-einladungslink.md)
