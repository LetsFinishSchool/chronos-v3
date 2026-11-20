---
id: RA-004
title: Gleichberechtigung und versehentliche Änderungen
status: entwurf
typ: risiko
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: []
---

# RA-004: Gleichberechtigung und versehentliche Änderungen

Risiko: Weil alle Mitglieder alles dürfen ([M-002](../05-modelle/M-002-berechtigungen.md)), können Mitglieder versehentlich oder böswillig Termine absagen oder Mitglieder entfernen. **Anforderung:** Alle Änderungen müssen sich rückgängig machen lassen, sofern fachlich möglich. Das gilt ausdrücklich auch für das Löschen von Teams und Terminen (Wiederherstellung samt Inhalten) ([F-017](../04-product-backlog/features/F-017-rueckgaengig-machen.md)). Nicht rückgängig machbar sind bereits versandte Benachrichtigungen; für sie gibt es eine Korrekturmeldung (?).

Maßnahme (entschieden): Änderungsverlauf mit Akteur und Benachrichtigung der Betroffenen bei Entfernen und Absagen.
