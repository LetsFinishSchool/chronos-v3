---
title: K-008 Sicherheit und Datenschutz
status: entwurf
quellen: [req42 QA-007, RB-006, Z-007, FA-013, RA-007, RA-010]
---

# K-008: Sicherheit und Datenschutz

**Vorgaben:**

- **Datensparsamkeit:** Nur nötige personenbezogene Daten (Keycloak-Kennung, Anzeigename, E-Mail, Gast-Name). Keine Daten von Kindern und Eltern ([Z-007](../../req42/01-ziele/Z-007-datensparsam-und-datenschutzkonform-betreiben.md)).
- **Datenschutzerklärung = Verarbeitung:** Sie beschreibt nur, was das System tut, und umgekehrt. Standardtexte DE/EN, Product Owner ist Verantwortlicher ([FA-013](../../req42/04-product-backlog/anforderungen/FA-013-rechtliche-seiten.md)). Impressum und Datenschutz sind ohne Anmeldung erreichbar.
- **Link-Token** (Einladung, Gast, Feed): nicht erratbar, widerrufbar, ablaufend; Gäste sehen nur, wofür der Link gilt ([QA-007](../../req42/06-qualitaet/QA-007-sicherheit-und-datenschutz.md)).
- **Zugangstoken** sind für Skripte der Seite nicht lesbar.
- **Backup** clientseitig verschlüsselt; Speicher in der EU.
- **Dritte mit personenbezogenen Daten:** Mailversand, Push-Dienste, KI-Anbieter; jeder braucht Eintrag in der Datenschutzerklärung.
- **Keine Geheimnisse im Repository** ([RB-008](../../req42/07-randbedingungen/RB-008-keine-geheimnisse-im-repository.md)).
- **Löschung:** Gelöschtes wird nach 30 Tagen endgültig entfernt (Wiederherstellungsfrist), auch aus dem Verlauf; Backups folgen dem Backup-Zyklus (**entschieden, PO 2026-11-20:** Backups bleiben im normalen Zyklus; die Löschung gilt mit Ablauf der Backup-Frist und wird in der Datenschutzerklärung offengelegt).

**Offen:** Löschkonzept bei Weggang einer Person, Auskunftsrecht, Aufbewahrung des Protokolls (Dauer), Datenschutz beim KI-Anbieter im Detail ([RA-008](../../req42/12-risiken-annahmen/RA-008-offene-fragen.md)), Schlüsselverwaltung für Backups ([E-010](../09-entscheidungen/01-offene-entscheidungen.md)).
