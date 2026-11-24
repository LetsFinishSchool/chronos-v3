---
id: QA-001
title: Ressourceneffizienz
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-005]
---

# QA-001: Ressourceneffizienz

**Qualitätsmerkmal (ISO 25010):** Leistungseffizienz (Ressourcennutzung)

## Szenario
Im Dauerbetrieb mit < 500 aktiven Nutzern benötigen alle Chronos-Komponenten einer Umgebung zusammen höchstens 1 vCPU und 1 GiB RAM; weniger ist besser. Das Budget schließt Datenbank und Hintergrundverarbeitung ein (?), nicht Keycloak.

## Messbar durch
Speicher- und CPU-Metriken des Clusters; Lasttest mit 500 Nutzern ([RB-003](../07-randbedingungen/RB-003-ressourcenbudget.md)).
