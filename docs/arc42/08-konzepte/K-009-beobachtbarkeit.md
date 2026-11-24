---
title: K-009 Beobachtbarkeit
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 QA-002, QA-001, QA-006, Z-002, SH-005]
---

# K-009: Beobachtbarkeit

**Vorgaben:**

- **Durchgängige Korrelations-ID** von der Anfrage (oder dem Zeitauslöser) über Operation, Ereignis, Benachrichtigung bis zur Zustellung und zum Kostenposten ([QA-002](../../req42/06-qualitaet/QA-002-nachvollziehbarkeit.md)).
- Der Weg eines Datums ist anhand von Logs und Protokoll **in Minuten** nachvollziehbar; Stichprobe: ein beliebiger Push/E-Mail ist auf Ereignis, Akteur und Zeitpunkt rückführbar.
- **Metriken:** CPU und Speicher gegen das Budget ([QA-001](../../req42/06-qualitaet/QA-001-ressourceneffizienz.md)), Zustellquote je Kanal (Ziel > 95 %), Benachrichtigungen je Person und Woche gegen Termine ([QA-010](../../req42/06-qualitaet/QA-010-benachrichtigungsbudget.md)), Kostenlimit.
- Betreiber wird benachrichtigt bei Erreichen des KI-Limits und bei Backup-Fehlern.
- Logs und Metriken enthalten keine unnötigen personenbezogenen Daten.

**Entschieden (PO 2026-11-20):** Der Bestand im Cluster wird genutzt ([E-012](../09-entscheidungen/01-offene-entscheidungen.md)). **Offen:** Aufbewahrungsdauer; Alarmierungsweg.
