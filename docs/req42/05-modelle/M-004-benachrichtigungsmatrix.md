---
id: M-004
title: Benachrichtigungsmatrix
status: entwurf
typ: modell
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-008]
---

# M-004: Benachrichtigungsmatrix

Jedes Ereignis hat genau einen benannten Auslöser und wird protokolliert ([QA-002](../06-qualitaet/QA-002-nachvollziehbarkeit.md)). Standardkanäle: Web Push und E-Mail; Einstellung je Person.

| Ereignis | Auslöser | Empfänger |
|---|---|---|
| Einladung zu Termin | Termin angelegt / Person hinzugefügt | Eingeladene |
| Termin geändert/verschoben | Änderung durch Mitglied | Eingeladene mit Antwort ≠ abgesagt |
| Termin abgesagt | Absage durch Mitglied | alle Eingeladenen |
| Rückmelde-Erinnerung | 1 Woche und 3 Tage vor Beginn | Eingeladene mit Rückmeldung offen |
| Wöchentliche Zusammenfassung | einmal pro Woche | Mitglieder mit offener Rückmeldung in den nächsten 14 Tagen |
| Ausbleibende Rückmeldung | einmalig 2 Tage vor Beginn | Leitung (Information, kein Handlungszwang) |
| Termin-Erinnerung | vom Benutzer eingestellt (je Termin überschreibbar) | Zugesagte und Zeitweise |
| Frist/Marke erreicht | Zeitpunkt der Marke | Team |
| Neue Terminnachricht | Nachricht geschrieben | Eingeladene |
| Terminfindung eröffnet | angelegt | Eingeladene |
| Terminfindung entschieden | Vorschlag festgelegt | Abstimmende |
| Zu Team hinzugefügt | Mitglied hinzugefügt / Linkbeitritt | betroffene Person |
| Termine durch Zeitraumsregel abgesagt | Regel angelegt / Termin im Zeitraum angelegt | Eingeladene (gebündelt) |
| Änderung rückgängig gemacht | Rücknahme | zuvor Informierte |
| Aus Team entfernt | Mitglied entfernt | betroffene Person, Team |

Das Benachrichtigungsbudget ([QA-010](../06-qualitaet/QA-010-benachrichtigungsbudget.md)) begrenzt die Standardeinstellung auf höchstens 2 × Termine der Woche je Person; Erinnerungen werden dazu gebündelt.
