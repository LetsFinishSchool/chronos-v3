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

Summe: 2 Korrekturschleifen (Abnahmesuite beim ersten vollständigen Lauf ohne Fehler).

PHASE-1-FERTIG 2026-11-20T20:42Z
