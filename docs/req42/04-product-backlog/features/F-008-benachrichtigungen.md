---
id: F-008
title: Benachrichtigungen
status: entwurf
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-002, SH-002, SH-003]
---

# F-008: Benachrichtigungen

**Story:** Als Beteiligte:r möchte ich über wichtige Ereignisse auf meinem bevorzugten Kanal informiert werden, damit ich nichts verpasse.

**Umfang:**
- Ereignisse und Empfänger nach [M-004](../../05-modelle/M-004-benachrichtigungsmatrix.md)
- Kanäle: Web Push und E-Mail verbindlich; Messenger (Telegram, WhatsApp) nur Option hinter einer Kanal-Abstraktion
- Erinnerungen vor Termin und vor Antwortfrist; Zeitpunkte stellt die Person selbst ein, über den Assistenten auch je Termin (gilt nur für diese Person)
- Benachrichtigungsbudget: höchstens 2 × Termine der Woche je Person in der Standardeinstellung ([Z-009](../../01-ziele/Z-009-benachrichtigungen-sparsam-halten.md), [QA-010](../../06-qualitaet/QA-010-benachrichtigungsbudget.md)); Person kann mehr einstellen
- Automatische Rückmelde-Erinnerungen und wöchentliche Zusammenfassung offener Rückmeldungen ([F-005](F-005-rueckmeldung.md))
- Einstellungen je Ereignis und Kanal
- Protokoll je Zustellung mit Auslöser

**Anforderung mit Akzeptanzkriterien:** [FA-008](../anforderungen/FA-008-benachrichtigungen.md)
