---
title: RB-003 Ressourcenlimits je Umgebung
datum: 2026-11-20
betrifft: docs/req42/07-randbedingungen/RB-003-ressourcenbudget.md
art: änderung
status: angenommen   # PO 2026-11-20
---

## Beobachtung
RB-003 nennt „ca. 1 vCPU und 1 GiB RAM für alle Chronos-Komponenten“. Der Product Owner hat für Kapitel 7 festgelegt: prod und staging haben je eigene, gleiche Limits von 1 vCPU und 1 GiB.

## Vorschlag
RB-003 klarstellen: Das Budget gilt je Umgebung (prod und staging je 1 vCPU / 1 GiB, gleich). QA-001 (Lasttest mit 500 Nutzern) prüfen, ob es sich auf eine Umgebung bezieht.

## Wirkung
Kapitel 7 (Verteilungssicht), Manifeste, QA-001.

## Entscheidung (Mensch)
Angenommen vom Product Owner am 2026-11-20. RB-003 und QA-001 (Dauerbetrieb je Umgebung) angepasst.
