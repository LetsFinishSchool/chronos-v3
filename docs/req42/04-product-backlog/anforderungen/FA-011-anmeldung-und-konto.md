---
id: FA-011
title: Anmeldung und Konto
status: entwurf
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-011]
---

# FA-011: Anmeldung und Konto

**Akzeptanzkriterien:**
1. Anmeldung erfolgt ausschließlich über Keycloak ([RB-002](../../07-randbedingungen/RB-002-identitaetsdienst-keycloak.md)); Chronos speichert keine Passwörter.
2. Die Sitzung läuft nicht sichtbar ab, solange die Person aktiv ist.
3. Chronos speichert nur die für den Betrieb nötigen Profildaten ([QA-007](../../06-qualitaet/QA-007-sicherheit-und-datenschutz.md)).

Feature: [F-011](../features/F-011-anmeldung-und-konto.md)
