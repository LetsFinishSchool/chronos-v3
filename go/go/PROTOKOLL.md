# Protokoll go

Start (UTC): 2026-11-20T20:30:16Z (laut .gestartet; Beginn der Arbeit 20:30)

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|
| S-1 (Operationsbeschreibung) | 2026-11-20T20:31Z | 2026-11-20T20:47Z | S1-Tests 7/7 |
| S-2/S-3 (Datenmodell, Transaktion, Verlauf, Rückgängig) | 2026-11-20T20:35Z | 2026-11-20T20:47Z | S2 6/6, S3 6/6 |

## Korrekturschleifen

_Eine Zeile je Schleife mit Kurzgrund._

1. (20:33) go get: Bibliotheksauswahl, keine Fehler
2. (20:42) Docker-Build: BuildKit fehlt (--mount) → Dockerfile ohne Cache-Mounts
3. (20:45) Laufzeit: huma-Registry Panik wegen gleichem Typnamen Empty in zwei Paketen → eigener SchemaNamer, op.Empty
