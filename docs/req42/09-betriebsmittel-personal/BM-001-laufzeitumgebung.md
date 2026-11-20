---
id: BM-001
title: Laufzeitumgebung
status: entwurf
typ: betriebsmittel
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [SH-005]
---

# BM-001: Laufzeitumgebung

| Betriebsmittel | Ausprägung |
|---|---|
| Cluster | k3s mit 3 Nodes: 1× 4 vCPU/8 GB, 2× 2 vCPU/4 GB; geteilt mit vielen Anwendungen |
| Budget für Chronos | ca. 1 vCPU, 1 GB RAM, besser weniger ([RB-003](../07-randbedingungen/RB-003-ressourcenbudget.md)) |
| Identitätsdienst | geteilter Keycloak, nicht im Budget ([RB-002](../07-randbedingungen/RB-002-identitaetsdienst-keycloak.md)) |
| Datenbank, Speicher, Backup-Ziel, Mailversand, Monitoring | Datenbank wird in arc42 entschieden; Backup täglich, clientseitig verschlüsselt, in S3-kompatiblen EU-Objektspeicher (Anbieter und Schlüsselverwaltung noch zu wählen, arc42); Mailversand über SMTP-Relay/EU-Anbieter; Umgebungen prod (bisheriges System) und staging im geteilten Cluster |

Kosten und Vertragslaufzeiten: [RA-008](../12-risiken-annahmen/RA-008-offene-fragen.md).
