---
id: M-005
title: Migrationsabbildung chronos-root → chronos-v3
status: entwurf
typ: modell
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-012]
---

# M-005: Migrationsabbildung chronos-root → chronos-v3

Ziel: [Z-006](../01-ziele/Z-006-bestandsdaten-verlustfrei-uebernehmen.md). Das Altschema wird bei der Umsetzung gegen die Datenbank von chronos-root geprüft (?).

| Altsystem | Neusystem | Bemerkung |
|---|---|---|
| Person (Keycloak-Kennung, Name, E-Mail) | Person (Konto) | Kennung bleibt gleich, Logins bleiben gültig |
| Termin | Termin der Art Treffen | Besitz/Team: aus Alt-Rollen und Gruppen ableiten (?) |
| Teilnahme (PENDING / APPROVED / REJECTED) | Rückmeldung (offen / zugesagt / abgesagt) | „zeitweise“ gibt es im Altsystem nicht |
| Teilnahme-Rolle (RESPONSIBLE, ATTENDANT, HELPER, GUEST) | Label am Termin (?) | Rollenrechte entfallen (gleichberechtigt) |
| Gruppe (+ Mitgliedschaft) | Team (+ Mitgliedschaft) | flach, Besitzer wird Mitglied |
| Gruppenteilnahme an Termin | Termin gehört dem Team | (?) |
| Mindestteilnehmerzahl, abgeleiteter Terminstatus | entfällt | [F-003](../04-product-backlog/features/F-003-termine.md) |
| Freundschaft | entfällt | |
| Nachricht | Terminnachricht | bleibt |
| Geräteabo (Push) | Kanal Web Push | optional |
| Benachrichtigungseinstellungen | Einstellungen je Ereignis/Kanal | grobe Abbildung (?) |
