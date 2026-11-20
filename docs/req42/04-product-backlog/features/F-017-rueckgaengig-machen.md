---
id: F-017
title: Gelöschtes wiederherstellen
status: entwurf
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-003, SH-002]
---

# F-017: Gelöschtes wiederherstellen

**Story:** Als Leitungsteam-Mitglied möchte ich gelöschte Teams und Termine wiederherstellen, damit Fehler, auch durch andere Mitglieder oder den Assistenten, folgenlos bleiben.

**Umfang:**
- Löschen von Teams und Terminen als Wiederherstellung samt Inhalten (Soft-Delete)
- Kein allgemeines Rückgängig für beliebige Änderungen (PO 2026-11-20)

**Entscheidung:**
- Gelöschte Objekte bleiben 30 Tage wiederherstellbar, danach endgültig gelöscht.
- Bei Wiederherstellung erhalten zuvor Informierte eine Korrekturnachricht.

**Anforderung mit Akzeptanzkriterien:** [FA-017](../anforderungen/FA-017-rueckgaengig-machen.md)
