---
id: FA-017
title: Änderungen rückgängig machen
status: entwurf
typ: anforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-017]
---

# FA-017: Änderungen rückgängig machen

**Akzeptanzkriterien:**
1. Jede Änderung im Änderungsverlauf bietet „rückgängig“, sofern der vorherige Zustand wiederherstellbar ist; sonst nennt das System den Grund.
2. Ein gelöschtes Team oder ein gelöschter Termin lässt sich 30 Tage lang wiederherstellen, inklusive Unter-Teams, Mitgliedschaften, Rückmeldungen, Labels und Nachrichten.
3. Rückgängig machen wird selbst protokolliert und kann ebenfalls rückgängig gemacht werden.
4. Gebündelte Änderungen (Bulk, Assistent, Regeln) lassen sich als Ganzes rückgängig machen.
5. Betroffene werden über die Rücknahme benachrichtigt, wenn sie zuvor über die Änderung informiert wurden.

Feature: [F-017](../features/F-017-rueckgaengig-machen.md)
