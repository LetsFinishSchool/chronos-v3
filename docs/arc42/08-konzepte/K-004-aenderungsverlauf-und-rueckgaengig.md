---
title: K-004 Änderungsverlauf und Wiederherstellung
status: entwurf
quellen: [req42 FA-017, FA-001, FA-015, FA-016, RA-004, M-001]
---

# K-004: Änderungsverlauf und Wiederherstellung

**Vorgaben** ([FA-017](../../req42/04-product-backlog/anforderungen/FA-017-rueckgaengig-machen.md), Stand PO 2026-11-20: kein allgemeines Rückgängig):

- Jede Änderung an Teams, Mitgliedschaften, Terminen, Veranstaltungen steht im Verlauf als Anzeige: **Akteur** (Person, „Assistent im Auftrag von …“ oder Regel), Aktion, Zeitpunkt, **Bündel-ID**. Ein Vorher-Zustand wird nicht gespeichert.
- **Wiederherstellung** gibt es für gelöschte Teams und Termine samt Unter-Teams, Mitgliedschaften, Rückmeldungen, Labels und Nachrichten (Soft-Delete, 30 Tage, danach endgültig gelöscht; [K-001](K-001-fachmodell-und-persistenz.md)). Gebündelte Löschungen lassen sich als Ganzes wiederherstellen.
- Betroffene, die zuvor über die Löschung informiert wurden, erhalten bei Wiederherstellung eine Korrekturnachricht ([K-003](K-003-ereignisse-und-benachrichtigung.md)). Bereits versandte Benachrichtigungen sind nicht zurücknehmbar.

**Architekturfolge:** Der Verlauf ist **Querschnitt der Operationsschicht**, nicht Aufgabe jedes Fachbereichs. Soft-Delete ist Teil des Fachmodells; eine neue Fachfunktion muss keinen Vorher-Zustand angeben.

**Entschieden:** E-007 erledigt durch die Reduzierung von FA-017 (kein Mechanismus für allgemeines Rückgängig).
