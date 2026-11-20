---
id: RB-002
title: Identitätsdienst Keycloak
status: entwurf
typ: randbedingung
kategorie: technisch
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: []
---

# RB-002: Identitätsdienst Keycloak

Anmeldung und Identität laufen über den geteilten Keycloak-Dienst; er zählt nicht zum Ressourcenbudget. Chronos führt keine eigene Passwortverwaltung. Gäste mit Einladungslink haben keine Keycloak-Identität. Verfügbarkeit und Betreiber des Dienstes: (?) ([SH-006](../02-stakeholder/SH-006-keycloak-betreiber.md)).
