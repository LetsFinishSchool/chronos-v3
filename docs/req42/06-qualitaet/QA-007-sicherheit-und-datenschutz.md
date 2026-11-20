---
id: QA-007
title: Sicherheit und Datenschutz
status: entwurf
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-007, Z-004]
---

# QA-007: Sicherheit und Datenschutz

**Qualitätsmerkmal (ISO 25010):** Sicherheit (Vertraulichkeit)

## Szenario
Einladungs- und Feed-Links enthalten nicht erratbare, widerrufbare Token; Gäste sehen nur, wofür der Link gilt. Es werden nur nötige personenbezogene Daten gespeichert (keine Daten von Kindern und Eltern). Zugangstoken sind nicht für Skripte der Seite lesbar.

## Messbar durch
Sicherheitstests der Link-Token; Datenschutzprüfung gegen Datenschutzerklärung ([RB-006](../07-randbedingungen/RB-006-datenschutz-und-impressum.md)).
