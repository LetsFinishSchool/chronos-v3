---
title: K-003 Ereignisse und Benachrichtigung
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 M-004, FA-005, FA-008, QA-002, QA-004, QA-010, Z-002, Z-009, Z-010]
---

# K-003: Ereignisse und Benachrichtigung

**Vorgaben:**

1. **Ereignis ≠ Benachrichtigung.** Ein fachliches Ereignis hat genau einen **benannten Auslöser** (Person, Assistent im Auftrag, Regel, Zeit) und wird festgehalten. Benachrichtigungen sind Reaktionen darauf ([M-004](../../req42/05-modelle/M-004-benachrichtigungsmatrix.md)).
2. **Protokoll** je Benachrichtigung: Auslöser, Empfänger, Kanal, Ergebnis, Zeitpunkt ([FA-008](../../req42/04-product-backlog/anforderungen/FA-008-benachrichtigungen.md)); Zielgröße: 100 % mit Auslöser.
3. **Höchstens eine Zustellung** je Ereignis, Empfänger und Kanal, auch bei Wiederholung nach Fehler. **Kein Ereignis geht verloren**, auch bei Neustart.
4. **Wiederholung begrenzt**, danach Ersatzkanal E-Mail, sofern die Person ihn erlaubt hat; Externe nur über hinterlegte Kanäle (?).
5. **Einstellung je Person** und Ereignisart; Standardkanäle Web Push und E-Mail; Messenger optional hinter derselben Kanal-Abstraktion.
6. **Sparsam:** Standard höchstens 2 × Termine der Woche je Person. Das System **plant** Erinnerungen und Sammelmeldungen entsprechend (Bündelung); es gibt keine Laufzeitsperre, Personen können mehr einstellen ([QA-010](../../req42/06-qualitaet/QA-010-benachrichtigungsbudget.md)).
7. **Zeitgesteuerte Ereignisse:** Rückmelde-Erinnerung (7 und 3 Tage), wöchentliche Zusammenfassung (14 Tage voraus), Leitungsinformation (2 Tage, einmalig), Termin-Erinnerung (vom Benutzer eingestellt, je Termin überschreibbar), Frist/Marke.
8. **Kosten:** Zustellung über E-Mail und Messenger erzeugt einen Kostenposten ([K-005](K-005-kostenerfassung.md)).
9. **Korrekturmeldung:** Versendete Benachrichtigungen sind nicht zurücknehmbar; bei Rücknahme einer Änderung erhalten zuvor Informierte eine Korrekturnachricht.
10. **Sprache** je Empfänger ([K-007](K-007-mehrsprachigkeit-und-zeitzonen.md)).

**Erweiterungspunkte:** neuer Kanal, neue Ereignisart (siehe [Veränderlichkeit](../04-loesungsstrategie/02-veraenderlichkeit.md)).

**Offen:** Festhalten und Zustellen (Mechanismus, Wiederholung, Idempotenzschlüssel), Zeitsteuerung, Planung des Budgets ([E-006](../09-entscheidungen/01-offene-entscheidungen.md)); Messung des Budgets je Person aus dem Protokoll.
