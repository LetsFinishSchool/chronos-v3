---
id: FA-008
title: Benachrichtigungen
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-008]
---

# FA-008: Benachrichtigungen

**Akzeptanzkriterien:**
1. Jede ausgelöste Benachrichtigung wird mit Auslöser, Empfänger, Kanal und Ergebnis protokolliert ([QA-002](../../06-qualitaet/QA-002-nachvollziehbarkeit.md)).
2. Ein Ereignis erzeugt je Empfänger und Kanal höchstens eine Zustellung, auch bei Wiederholung nach Fehler ([QA-004](../../06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md)).
3. Schlägt der Kanal Web Push fehl oder fehlt ein Abo, bekommt die Person E-Mail, wenn sie diesen Kanal erlaubt hat.
4. Externe ohne Konto werden nur über hinterlegte Kanäle erreicht (?).
5. Jede Zustellung über einen kostenpflichtigen Kanal (E-Mail, Messenger) wird als Kostenposten der auslösenden Person oder dem Team zugeordnet ([RB-010](../../07-randbedingungen/RB-010-kostenzuordnung.md)).
6. Jede Person kann Kanäle je Ereignisart ein- und ausschalten.
7. In der Standardeinstellung erhält eine Person je Woche höchstens doppelt so viele Benachrichtigungen wie Termine in der Woche; mehrere Erinnerungen werden dazu gebündelt ([QA-010](../../06-qualitaet/QA-010-benachrichtigungsbudget.md)). Jede Person kann mehr einstellen.
8. Erinnerungszeitpunkte stellt jede Person selbst ein; über den Assistenten sind abweichende Zeiten je Termin möglich, die nur für diese Person gelten.

Feature: [F-008](../features/F-008-benachrichtigungen.md)
