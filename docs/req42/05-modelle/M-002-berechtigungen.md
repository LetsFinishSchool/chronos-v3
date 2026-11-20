---
id: M-002
title: Berechtigungen
status: entwurf
typ: modell
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-001, F-002]
---

# M-002: Berechtigungen

Alle Mitglieder eines Teams sind gleichberechtigt. Labels ([F-007](../04-product-backlog/features/F-007-labels.md)) geben keine Rechte.

| Aktion | Wer |
|---|---|
| Team, Termine, Veranstaltungen, Terminfindungen des Teams lesen, anlegen, ändern, absagen | jedes Mitglied des Teams |
| Mitglieder einladen, Einladungslink erzeugen/widerrufen | jedes Mitglied |
| Mitglieder entfernen, Team löschen | jedes Mitglied; jede Änderung steht mit Akteur im Änderungsverlauf |
| Unter-Team anlegen | jedes Mitglied des übergeordneten Teams |
| Auf Termin antworten, Nachricht schreiben | eingeladene Mitglieder und Personen mit gültigem Link |
| Eigene Antwort, Einstellungen, Feed-Link ändern | nur die Person selbst |

**Vererbung:** Mitgliedschaft wird **nach oben** vererbt: Mitglieder eines Unter-Teams sind auch Mitglieder aller übergeordneten Teams. Gäste über Einladungslink sind nur Mitglied des konkreten Teams, für das sie eingeladen wurden.

**Missbrauchsschutz:** Weil alle alles dürfen, gibt es einen Änderungsverlauf und Benachrichtigung bei Entfernen/Absagen ([RA-004](../12-risiken-annahmen/RA-004-gleichberechtigung-und-versehentliche-aenderungen.md), [QA-002](../06-qualitaet/QA-002-nachvollziehbarkeit.md)).
