# Protokoll rust

Start (UTC): 2026-11-20T20:30:16Z

Zeiten stammen aus den Zeitstempeln der Befehle bzw. Commits; die Aufgaben wurden nicht strikt nacheinander, sondern in einem Zug geschrieben und danach gemeinsam an der Suite geprüft. „Beginn“ = Beginn des Schreibens, „Ende“ = erster grüner Suitelauf der Aufgabe.

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|
| S-1 Operationsbeschreibung, Aufruf | 20:31 | 20:49 | `core/ops.rs`, S1 7/7 |
| S-2 Team-Baum | 20:36 | 20:49 | rekursive CTE, S2 6/6 |
| S-3 Transaktion, Verlauf, Rückgängig | 20:38 | 20:49 | S3 6/6 (1 manuell übersprungen) |
| S-4 Worker und Kanäle | 20:41 | 20:49 | M14 6/6; M15 im Container 1/1 (20:55); K5 1/1 (20:55) |
| S-5 RRULE | 20:36 | 20:51 | K2 29/29 nach Vorprüfung |
| S-6 Anmeldung | 20:43 | 20:51 | K4 4/4 nach 302-Korrektur |
| S-7 KI | 20:40 | 20:52 | K6 1/1 (2 Proxy-Anfragen insgesamt, kein 429) |
| S-9 Architekturregel | 20:52 | 20:53 | `make arch-check`, Verstoß getestet |
| S-10 Brücke | 20:49 | 20:53 | S10 3/3 |
| S-8 Lastlauf (Selbstkontrolle) | 20:56 | 20:57 | 52 Anfragen/s, 0 Fehler |

## Korrekturschleifen

1. Übersetzer: sqlx 0.9 verlangt `AssertSqlSafe` für dynamische SQL; `OnceLock` im `inventory`-Static nicht erlaubt (Cache ausgelagert).
2. Laufzeit: jsonwebtoken 12 ohne Crypto-Backend (Panik) → Feature `rust_crypto`.
3. Test: `/auth/login` lieferte 303 statt 302 (axum `Redirect::to`) → eigener 302.
4. Test: K2 ungültige RRULEs (`COUNT`+`UNTIL`, `INTERVAL=0`, `BYMONTHDAY=0`) von `rrule` akzeptiert → Vorprüfung.
5. Laufzeit: `make bridge` scheiterte an Node-`fetch` („bad port“ 10080) → `node:http`.
6. Test: M15 schlug beim Lauf mit Host-Prozessen fehl (Logs nur im Container lesbar); kein Codefehler, Wiederholung mit Container-Image war grün (zählt als Umgebungsschleife).

Hindernisse: keine Rückfragen; K3 nicht Teil der Aufgabe.

PHASE-1-FERTIG: siehe unten.
