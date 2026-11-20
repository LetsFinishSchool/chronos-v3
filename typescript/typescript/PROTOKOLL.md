# Protokoll typescript

Start (UTC): 2026-11-20T20:30:16Z

Zeiten sind aus der Sitzungsuhr entnommen und teilweise gerundet (Aufgaben überlappten, weil Operationsschicht, Datenmodell und Worker in einem Zug entstanden); die Abnahmeläufe sind genau.

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|
| Lesen von Briefing, V-1, Suite | 20:30 | 20:32 | |
| S-5 RRULE (vorgezogen, Golden-Test unter vitest) | 20:32 | 20:34 | 27/27 beim ersten Lauf |
| S-1 Operationsbeschreibung und Aufruf | 20:34 | 20:36 | `defineOperation`, Registry, Vorschau per Rollback |
| S-2/S-3 Datenmodell, Transaktion, Verlauf, Rückgängig | 20:34 | 20:37 | Migration, `recordChange`, Fehlerinjektion |
| S-4 Worker und Kanäle | 20:37 | 20:38 | Lease-Warteschlange in PostgreSQL |
| S-6 Anmeldung | 20:36 | 20:38 | jose + openid-client |
| S-7 KI | 20:36 | 20:38 | Anthropic-SDK über Schutz-Proxy; K6 bestanden |
| S-9 Architekturregel | 20:39 | 20:40 | dependency-cruiser; Verstoß getestet (Exit 2), ohne Verstoß 0 |
| S-10 Brücke | 20:38 | 20:39 | json-schema-to-typescript; 3/3 |
| S-8 Lastlauf (Selbstkontrolle) | 20:40 | 20:41 | 6000 Aufrufe, 0 Fehler, p99 198 ms |
| Abnahmesuite komplett | 20:39 | 20:41 | alle Tests grün (K5: 32 wirksam beim Abbruch, 7 Duplikate) |

KI-Proxy: kein 429; nur wenige Aufrufe (K6 einmal pro Lauf).

## Korrekturschleifen

1. Übersetzer: Kysely-Migrationstypen müssen aus `kysely/migration` kommen; `Generated<Ts>` doppelt verschachtelt (Typfehler).
2. Laufzeit im Container: ESM-Importfehler bei `rrule` (CommonJS, Default-Import) und `web-push` (nur benannte Exporte) – unter tsx/vitest nicht aufgefallen.

3. Phase 2, Test (K5 im vollen Phase-1-Lauf): Nach `SIGKILL` blieben laufende Zustellungen bis zum Ablauf der 15-s-Lease gesperrt, das Zustellprotokoll hatte noch keine Erfolgszeile. Behoben: Sperren tragen eine Worker-Kennung (`locked_by`, Hostname/`WORKER_ID`); ein neu gestarteter Worker gibt eigene Sperren sofort frei (Migration 002). Der Fehler war schon in Phase 1 latent (K5 bestand dort nur zufällig bei einzelnem Lauf).

Summe: 3 Korrekturschleifen.

PHASE-1-FERTIG 2026-11-20T20:42Z

## Phase 2 (N-1 `appointment.reschedule`)

Beginn 2026-11-20T20:53Z, Ende ca. 20:59Z. Berührt: **eine** Datei (`src/domain/ops/appointment.ts`, ~20 Zeilen, eine `defineOperation`-Beschreibung). Ohne weitere Handarbeit erscheint die Operation in `/api/v1/operations`, `/api/v1/ai/tools` (N1 2/2) und – nach `make bridge` – in `bridge/generated/operations.ts` (19 Operationen); Rückgängig funktioniert über die generische Wiederherstellung. Lücke in der Operationsbeschreibung aus Phase 1: keine. Phase 1 danach erneut vollständig grün (zweimal).
Zusatzänderung (kein N-1-Aufwand): K5-Korrektur oben (`worker.ts`, `db.ts`).

PHASE-2-FERTIG 2026-11-20T20:59:14Z

FERTIG 2026-11-20T20:59:17Z
