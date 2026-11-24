---
id: SC-002
title: Im und nicht im Scope
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: scope
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [SH-001]
---

# SC-002: Im und nicht im Scope

**Im Scope:**
- Teams und beliebig tiefe Unter-Teams, Mitglieder, Einladungslinks ([F-001](https://github.com/LetsFinishSchool/chronos-v3/issues/8), [F-002](https://github.com/LetsFinishSchool/chronos-v3/issues/49)).
- Interne Termine (Treffen mit Rückmeldung, Fristen und Marken) und Veranstaltungen als Klammer ([F-003](https://github.com/LetsFinishSchool/chronos-v3/issues/13), [F-004](https://github.com/LetsFinishSchool/chronos-v3/issues/62)).
- Rückmeldung Zusage/Absage/Zeitweise, Terminfindung per Abstimmung ([F-005](https://github.com/LetsFinishSchool/chronos-v3/issues/17), [F-006](https://github.com/LetsFinishSchool/chronos-v3/issues/57)).
- Labels für Rollen und Aufgaben ([F-007](https://github.com/LetsFinishSchool/chronos-v3/issues/66)).
- Benachrichtigung über Web Push und E-Mail, Kalender-Feed, Terminnachrichten ([F-008](https://github.com/LetsFinishSchool/chronos-v3/issues/22) bis [F-010](https://github.com/LetsFinishSchool/chronos-v3/issues/72)).
- Serientermine mit vollen RRULE-Regeln und Schulferien-Ausnahmen ([F-014](https://github.com/LetsFinishSchool/chronos-v3/issues/75)).
- KI-Assistent für komplexe Operationen und Bulk-Aktionen, dauerhafte Zeitraumsregeln ([F-015](https://github.com/LetsFinishSchool/chronos-v3/issues/80), [F-016](https://github.com/LetsFinishSchool/chronos-v3/issues/88)).
- Wiederherstellen gelöschter Teams und Termine, Kostenerfassung je Benutzer/Team ([F-017](https://github.com/LetsFinishSchool/chronos-v3/issues/32), [F-018](https://github.com/LetsFinishSchool/chronos-v3/issues/39)).
- Mehrsprachigkeit Deutsch/Englisch ([RB-001](../07-randbedingungen/RB-001-mehrsprachigkeit.md)).
- Anmeldung, Datenübernahme, rechtliche Seiten ([F-011](https://github.com/LetsFinishSchool/chronos-v3/issues/28) bis [F-013](https://github.com/LetsFinishSchool/chronos-v3/issues/31)).

**Nicht im Scope (bewusst):**
- **Kinder und Eltern** als Nutzer. Chronos verwaltet keine Teilnehmer von Veranstaltungen, keine Anmeldungen und keine öffentliche Veranstaltungsseite; eine Veranstaltung ist nur interne Klammer und Planungsobjekt der Leitung.
- Freundschaften und persönliche Netzwerke (entfallen gegenüber chronos-root).
- Allgemeiner Kalender, Chat-Ersatz außerhalb von Terminen.
- Eigene Benutzer- und Passwortverwaltung (liegt bei Keycloak).
- Allgemeines Rückgängig für jede Änderung (nur gelöschte Objekte sind wiederherstellbar, [FA-017](https://github.com/LetsFinishSchool/chronos-v3/issues/32)).

**Optional / später:** Messenger-Kanäle (Telegram, WhatsApp), Übernahme der Push-Geräteabos aus chronos-root.
