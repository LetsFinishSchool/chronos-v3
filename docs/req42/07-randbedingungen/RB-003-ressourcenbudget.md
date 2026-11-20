---
id: RB-003
title: Ressourcenbudget
status: entwurf
typ: randbedingung
kategorie: technisch
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: []
---

# RB-003: Ressourcenbudget

Für alle Chronos-Komponenten stehen **je Umgebung** (prod und staging, gleich ausgestattet) etwa 1 vCPU und 1 GiB RAM zur Verfügung, besser weniger. Der Cluster (k3s, 3 Nodes: 1× 4 vCPU/8 GB, 2× 2 vCPU/4 GB) wird von vielen Anwendungen geteilt. Folge: Technologien mit hohem Grundspeicher (z. B. JVM-Stack) sind zu begründen ([QA-001](../06-qualitaet/QA-001-ressourceneffizienz.md)).
