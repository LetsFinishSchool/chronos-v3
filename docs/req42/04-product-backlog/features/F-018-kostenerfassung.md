---
id: F-018
title: Kostenerfassung
status: entwurf
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-005, SH-001, SH-005]
---

# F-018: Kostenerfassung

**Story:** Als Product Owner möchte ich sehen, welche Kosten wodurch entstanden sind, damit ich sie zuordnen und begrenzen kann.

**Umfang:**
- Einzelposten je kostenverursachendem Aufruf (WhatsApp/Messenger, E-Mail, KI)
- Zuordnung je Benutzer, ersatzweise je Team
- Auswertung und Rekonstruktion bis zum Auslöser

**Entscheidung:** Der Betreiber trägt die Kosten; KI-Nutzung wird über ein Monatslimit je Team begrenzt und in der Kostenerfassung angezeigt.

**Entscheidung:** Obergrenze für Zusatzkosten 10 € pro Monat; bei Erreichen pausiert die KI bis Monatsende und der Betreiber wird benachrichtigt, Backup und E-Mail laufen weiter ([RA-009](../../12-risiken-annahmen/RA-009-budget-und-abhaengigkeit-von-keycloak.md)).

**Offen:**
- Abrechnung gegenüber Teams (falls gewünscht)

**Anforderung mit Akzeptanzkriterien:** [FA-018](../anforderungen/FA-018-kostenerfassung.md)
