# Protokoll go

Start (UTC): 2026-11-20T20:30:16Z (laut .gestartet; Beginn der Arbeit 20:30)

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|
| S-1 (Operationsbeschreibung) | 2026-11-20T20:31Z | 2026-11-20T20:47Z | S1-Tests 7/7 |
| S-2/S-3 (Datenmodell, Transaktion, Verlauf, Rückgängig) | 2026-11-20T20:35Z | 2026-11-20T20:47Z | S2 6/6, S3 6/6 |
| S-4 (Worker, Kanäle) | 2026-11-20T20:38Z | 2026-11-20T20:48Z | M14 6/6, K5 1/1 (Abbruch bei 24 wirksamen, 6–8 Duplikat-Versuche) |
| S-5 (RRULE) | 2026-11-20T20:36Z | 2026-11-20T20:48Z | K2 29/29, kein Nachbessern nötig |
| S-6 (Anmeldung) | 2026-11-20T20:40Z | 2026-11-20T20:48Z | K4 4/4 |
| S-7 (KI) | 2026-11-20T20:41Z | 2026-11-20T20:49Z | K6 1/1 (ein Aufruf des Proxys je Testlauf, 2 Läufe insgesamt, kein 429) |
| S-9 (Architekturregel) | 2026-11-20T20:43Z | 2026-11-20T20:49Z | `make arch-check`; Negativprobe (Import von channels in domain) → Exit 1 |
| S-10 (Brücke) | 2026-11-20T20:43Z | 2026-11-20T20:48Z | S10 3/3 |
| S-8 (Lastlauf, Selbstkontrolle) | 2026-11-20T20:48Z | 2026-11-20T20:49Z | 16 Threads, 30 s, 59/s, 0 Fehler, p95 475 ms |

Hinweis: Beginn-/Endzeiten der Blöcke S-4 bis S-10 sind gerundet (Blöcke wurden überlappend geschrieben und gemeinsam getestet; Testläufe 20:47–20:49 UTC).


## Korrekturschleifen

_Eine Zeile je Schleife mit Kurzgrund._

1. (20:36) Übersetzer: go.sum-Eintrag für pgx/puddle fehlt → `go mod tidy`
2. (20:40) Übersetzer: `notification.list` – CorrelationID ist `pgtype.Text`, nicht `*string` → Typ angepasst
3. (20:41) Übersetzer: go.sum-Einträge für go-oidc/go-jose fehlen → `go get`
4. (20:42) Docker-Build: BuildKit fehlt (`--mount`) → Dockerfile ohne Cache-Mounts
5. (20:45) Laufzeit: huma-Registry-Panik wegen gleichem Typnamen `Empty` in zwei Paketen → eigener SchemaNamer, `op.Empty`

Danach liefen alle Abnahmetests ohne weitere Korrekturen (Gesamtlauf 20:48 UTC: 65 Tests, 1 manuell übersprungen).

## Hindernisse

- Ein Shell-Aufruf mit mehreren Heredocs wurde vom Werkzeug-Schutz abgelehnt (nichts ausgeführt); Dateien danach einzeln geschrieben. Keine Auswirkung auf das Ergebnis.
- Kein KI-Budgetproblem (kein 429).

PHASE-1-FERTIG: 2026-11-20T20:49:40Z

## Phase 2 (N-1 appointment.reschedule)

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|
| N-1 | 2026-11-20T20:53Z | 2026-11-20T20:56:23Z | 1 Datei geändert (go/internal/domain/appointment.go, +42 Zeilen: Parametertyp und eine op.Register-Gruppe). Phase 2: N1 2/2; Phase 1 danach unverändert grün (65 Tests, 1 manuell übersprungen). |

Korrekturschleifen Phase 2: 0. Lücke der Operationsbeschreibung: keine. Die Operation erschien ohne Handarbeit in /api/v1/operations, /api/v1/ai/tools und (nach make bridge) in bridge/generated/operations.ts; Rückgängig funktioniert über das generische history.undo.

PHASE-2-FERTIG: 2026-11-20T20:56:23Z
FERTIG: 2026-11-20T20:56:23Z
