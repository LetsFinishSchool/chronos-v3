---
title: Folgeänderungen aus der Reduzierung von FA-017 auf Soft-Delete
datum: 2026-11-20
betrifft: docs/req42 (FA-001, FA-014, FA-015, SC-002, RA-004, RA-010, RM-001, F-001, M-004), docs/arc42 (K-002, K-003, K-004, K-006, Kapitel 1.2, 4, 6, 11, 12, ADR-001/002)
art: änderung
status: angenommen   # PO 2026-11-20
---

## Beobachtung
FA-017/F-017 sind am 2026-11-20 auf Wiederherstellung gelöschter Objekte (Soft-Delete, 30 Tage) reduziert. Mehrere Texte verweisen noch auf „alles rückgängig machbar“. Historische Einträge (RA-008 Runde 5/6) bleiben unverändert, sie dokumentieren den damaligen Stand.

## Vorschlag (alt → neu)

**req42**
- FA-001 AK 6: „… und sind über „Rückgängig“ wiederherstellbar“ → „… und sind 30 Tage wiederherstellbar ([FA-017](FA-017-rueckgaengig-machen.md))“.
- F-001 Entscheidung: „alles ist über „Rückgängig“ wiederherstellbar“ → „gelöschte Teams und Termine sind 30 Tage wiederherstellbar“.
- FA-014 AK 5: „Jede Änderung an Serien ist rückgängig machbar“ → „Eine gelöschte Serie lässt sich 30 Tage wiederherstellen“.
- FA-015 AK 5: „… und sind rückgängig machbar“ → „… und gelöschte Objekte sind wiederherstellbar; eine Änderung des Assistenten wird nur durch die Vorschau/Freigabe abgesichert“.
- SC-002: „Rückgängig machen aller Änderungen“ → „Wiederherstellen gelöschter Teams und Termine“; unter „nicht im Scope“: allgemeines Rückgängig für jede Änderung.
- RA-004: „Alle Änderungen müssen sich rückgängig machen lassen, sofern fachlich möglich“ → „Gelöschtes ist wiederherstellbar; Änderungen sind im Änderungsverlauf nachvollziehbar und die Betroffenen werden benachrichtigt“.
- RA-010: Maßnahme „Rückgängig“ → „Wiederherstellung gelöschter Objekte“.
- RM-001: „Änderungsverlauf mit Rückgängig-machen“ → „Änderungsverlauf und Wiederherstellen gelöschter Objekte“.
- M-004: Zeile „Änderung rückgängig gemacht / Rücknahme“ → „Objekt wiederhergestellt / Wiederherstellung“.

**arc42**
- K-004 (Titel „Änderungsverlauf und Wiederherstellung“): Verlauf bleibt als Anzeige (Akteur, Aktion, Zeitpunkt, Bündel-ID); kein Vorher-Zustand, kein allgemeines Rückgängig. Wiederherstellung nur für gelöschte Teams/Termine samt Inhalten, 30 Tage; Korrekturnachricht an zuvor Informierte; „Offen: Mechanismus (E-007)“ entfällt.
- K-002, K-006, K-011, Glossar (Bündel): „Rückgängig“/„als Ganzes rückgängig“ → „Wiederherstellung gelöschter Objekte“ bzw. Bündel nur zur Nachvollziehbarkeit.
- Kapitel 4.2 (Fachfunktionen): „rückgängig machbar“ entfällt als Pflicht je Funktion; Kapitel 6 L-6 „Rückgängig machen“ → „Gelöschtes wiederherstellen“ (nur Wiederherstellung, kein Vorher-Zustand).
- Kapitel 1.2 und ADR-001: Spannung „alles rückgängig“ gegen Änderungsaufwand entfällt. ADR-002: Treiber „Verlauf und Rückgängig“ → „Verlauf und Wiederherstellung“.
- Kapitel 11: R-A3 „Alles rückgängig kostet je Funktion“ entfällt oder wird zu „Wiederherstellung gelöschter Objekte muss alle abhängigen Inhalte umfassen“.

## Wirkung
Fachliche Texte und Architekturtexte sind konsistent mit FA-017. Der Aufwandsfaktor „Vorher-Zustand je Funktion“ entfällt und stärkt die Änderbarkeit (ADR-001).

## Entscheidung (Mensch)
Angenommen vom Product Owner am 2026-11-20 und umgesetzt (req42 und arc42).
