---
title: M-005 Rollen und Einstellungen werden bei Migration verworfen
datum: 2026-11-20
betrifft: docs/req42/05-modelle/M-005-migrationsabbildung.md
art: änderung
status: angenommen   # PO 2026-11-20
---

## Beobachtung
In arc42 K-010 waren drei Abbildungen unsicher. Product Owner entschied am 2026-11-20 im Gespräch: Termine werden je Team dupliziert, Teilnahme-Rollen werden verworfen, Einstellungen werden verworfen (Standardwerte im Neuschema). Der Probelauf läuft in staging mit echten Altdaten.

## Vorschlag
M-005 entsprechend anpassen (Abbildung Rolle → Label entfällt, Einstellungen entfallen, Termin-Besitz je Team = Duplikat je Team). Prüfen, ob FA-012 und RA-005 Verluste (Rollen, Einstellungen) ausdrücklich nennen müssen. Hinweis: Echte Altdaten in staging berühren K-008 (Datenschutz); Zugriff und Löschung nach dem Probelauf regeln.

## Wirkung
K-010, Importwerkzeug (E-017), Abnahme der Migration.

## Entscheidung (Mensch)
Angenommen vom Product Owner am 2026-11-20 und in docs/req42 übernommen.
