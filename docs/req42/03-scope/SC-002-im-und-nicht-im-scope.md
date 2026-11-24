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
- Teams und beliebig tiefe Unter-Teams, Mitglieder, Einladungslinks ([F-001](../04-product-backlog/features/F-001-teams-und-unter-teams.md), [F-002](../04-product-backlog/features/F-002-mitglieder-und-einladungslink.md)).
- Interne Termine (Treffen mit Rückmeldung, Fristen und Marken) und Veranstaltungen als Klammer ([F-003](../04-product-backlog/features/F-003-termine.md), [F-004](../04-product-backlog/features/F-004-veranstaltungen.md)).
- Rückmeldung Zusage/Absage/Zeitweise, Terminfindung per Abstimmung ([F-005](../04-product-backlog/features/F-005-rueckmeldung.md), [F-006](../04-product-backlog/features/F-006-terminfindung.md)).
- Labels für Rollen und Aufgaben ([F-007](../04-product-backlog/features/F-007-labels.md)).
- Benachrichtigung über Web Push und E-Mail, Kalender-Feed, Terminnachrichten ([F-008](../04-product-backlog/features/F-008-benachrichtigungen.md) bis [F-010](../04-product-backlog/features/F-010-terminnachrichten.md)).
- Serientermine mit vollen RRULE-Regeln und Schulferien-Ausnahmen ([F-014](../04-product-backlog/features/F-014-serientermine.md)).
- KI-Assistent für komplexe Operationen und Bulk-Aktionen, dauerhafte Zeitraumsregeln ([F-015](../04-product-backlog/features/F-015-ki-assistent.md), [F-016](../04-product-backlog/features/F-016-zeitraumsregeln.md)).
- Wiederherstellen gelöschter Teams und Termine, Kostenerfassung je Benutzer/Team ([F-017](../04-product-backlog/features/F-017-rueckgaengig-machen.md), [F-018](../04-product-backlog/features/F-018-kostenerfassung.md)).
- Mehrsprachigkeit Deutsch/Englisch ([RB-001](../07-randbedingungen/RB-001-mehrsprachigkeit.md)).
- Anmeldung, Datenübernahme, rechtliche Seiten ([F-011](../04-product-backlog/features/F-011-anmeldung-und-konto.md) bis [F-013](../04-product-backlog/features/F-013-rechtliche-seiten.md)).

**Nicht im Scope (bewusst):**
- **Kinder und Eltern** als Nutzer. Chronos verwaltet keine Teilnehmer von Veranstaltungen, keine Anmeldungen und keine öffentliche Veranstaltungsseite; eine Veranstaltung ist nur interne Klammer und Planungsobjekt der Leitung.
- Freundschaften und persönliche Netzwerke (entfallen gegenüber chronos-root).
- Allgemeiner Kalender, Chat-Ersatz außerhalb von Terminen.
- Eigene Benutzer- und Passwortverwaltung (liegt bei Keycloak).
- Allgemeines Rückgängig für jede Änderung (nur gelöschte Objekte sind wiederherstellbar, [FA-017](../04-product-backlog/anforderungen/FA-017-rueckgaengig-machen.md)).

**Optional / später:** Messenger-Kanäle (Telegram, WhatsApp), Übernahme der Push-Geräteabos aus chronos-root.
