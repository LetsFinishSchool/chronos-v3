---
title: FA-017 Verlauf und Rückgängig überprüfen
datum: 2026-11-20
betrifft: docs/req42/04-product-backlog/anforderungen (FA-017), docs/arc42 K-004
art: änderung
status: angenommen   # PO 2026-11-20 (Soft-Delete)
---

## Beobachtung
Bei der Abwägung von E-007 (Mechanismus für Verlauf und Rückgängig) hat der Product Owner entschieden: Die Komplexität eines allgemeinen Verlaufs mit Rückgängig steht nicht im Verhältnis zum Wert. Quelle: Session 2026-11-20, Pro/Contra zu Vorher-Zustand, Differenzen, Ereignisprotokoll.

## Vorschlag
Als **offene Entscheidung in den Anforderungen** aufnehmen: Muss ein allgemeines Rückgängig für alle Änderungen möglich sein, oder genügt die Wiederherstellung gelöschter Objekte (Soft-Delete, 30 Tage)? Bis zur Klärung bleibt E-007 in arc42 zurückgestellt. K-004 und die Verweise in K-002/K-003 (Missbrauchsschutz über Verlauf und Rückgängig) wären bei einer Reduzierung anzupassen.

## Wirkung
Betrifft FA-017, K-004, K-002 (Missbrauchsschutz), K-003 (Benachrichtigung bei Rücknahme), K-008 (Löschfrist). Ein Soft-Delete-Modell würde E-007 weitgehend auflösen.

## Entscheidung (Mensch)
Angenommen vom Product Owner am 2026-11-20: FA-017 und F-017 auf Soft-Delete reduziert. Folgearbeiten: weitere Verweise auf „Rückgängig“ in req42 (Z-003, SC-002, RA-004, RA-010, FA-001, FA-014, FA-015, M-004, RM-001, F-001) und arc42 (K-002, K-003, K-004, Kapitel 1/4/5/6/11, ADR-001) prüfen.
