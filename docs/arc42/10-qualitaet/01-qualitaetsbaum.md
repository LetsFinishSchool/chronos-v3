---
title: Qualitätsbaum
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 QA-001..QA-010]
---

# 10.1 Qualitätsbaum

```mermaid
flowchart LR
  Q((Qualität))
  Q --> W[Wartbarkeit]
  Q --> E[Leistungseffizienz]
  Q --> Z[Zuverlässigkeit]
  Q --> G[Gebrauchstauglichkeit]
  Q --> S[Sicherheit]
  Q --> F[Funktionale Eignung]
  W --> QA2[QA-002 Nachvollziehbarkeit]
  W --> QA3[QA-003 Änderbarkeit, Modularität]
  E --> QA1[QA-001 Ressourceneffizienz]
  E --> QA8[QA-008 Antwortzeit]
  Z --> QA4[QA-004 Zuverlässige Benachrichtigung]
  Z --> QA6[QA-006 Datensicherung]
  G --> QA5[QA-005 Bedienbarkeit mobil]
  G --> QA10[QA-010 Benachrichtigungsbudget]
  S --> QA7[QA-007 Sicherheit und Datenschutz]
  F --> QA9[QA-009 Kostentransparenz]
```

Das Gewicht der Zweige legt [ADR-001](../09-entscheidungen/ADR-001-prioritaet-der-qualitaetsziele.md) fest. Qualitätsziele auf oberster Ebene: [1.2](../01-einfuehrung/02-qualitaetsziele.md).
