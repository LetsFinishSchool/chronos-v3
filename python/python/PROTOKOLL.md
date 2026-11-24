# Protokoll python

Start (UTC): 2026-11-23T08:54:26Z (Datei `.gestartet`)

Zeiten sind aus den Zeitstempeln meiner Befehle (`date -u`) und Commits rekonstruiert (±1–2 min). Der Code der Aufgaben
S-1 bis S-7 und S-10 entstand in einem zusammenhängenden Block; eine genaue Trennung je Aufgabe war nicht möglich.

| Aufgabe | Beginn (UTC) | Ende (UTC) | Anmerkung |
|---|---|---|---|
| S-1 Operationsbeschreibung, Aufruf | 08:55 | 09:04 | Registry, Executor, Endpunkte, Werkzeugliste (Abnahme S1: 7/7) |
| S-2 Team-Baum | 08:55 | 09:04 | rekursive CTEs, Berechtigung zentral in `core/access.py` (6/6) |
| S-3 Transaktion, Verlauf, Rückgängig | 08:55 | 09:04 | eine Transaktion, Fehlerinjektion, generisches Rückgängig (6/6, 1 manuell) |
| S-4 Worker und Kanäle | 08:55 | 09:04 | Warteschlange auf PostgreSQL; M-14 6/6, M-15 1/1, K5 1/1 |
| S-5 RRULE | 08:55 | 09:04 | dateutil; K2 29/29 |
| S-6 Anmeldung | 08:55 | 09:04 | authlib + PyJWT; K4 4/4 |
| S-7 KI | 08:55 | 09:07 | K6 nach Korrekturschleife 2 bestanden (2 Anfragen am Proxy) |
| S-9 Architekturregel | 09:05 | 09:06 | import-linter; Verstoß gezielt eingebaut → Exit 2, ohne → 0 |
| S-10 Brücke | 09:05 | 09:06 | json-schema-to-typescript; S10 3/3 |
| S-8 Lastlauf (Selbstkontrolle) | 09:07 | 09:08 | 1048 Anfragen, keine Fehler |

Gesamtlauf der Abnahmesuite 09:08:07–09:08:57: 65 Tests, alle bestanden (1 manuell übersprungen).

## Korrekturschleifen

Anzahl: **4**

1. `uv lock` im Container scheiterte mit „Permission denied“ (uv.lock gehörte root) → Datei gelöscht, Container mit Benutzer-ID.
2. K6 schlug fehl („unbekanntes Feld title“): Schema-Bereinigung entfernte das Feld `title` → `_inline` unterscheidet Schlüsselwort und Feldname.
3. `make test`: `No module named 'chronos'` → `pythonpath = ["."]` in der pytest-Konfiguration.
4. (Phase 2, Regressionslauf) K5 schlug einmal fehl: Zustellprotokoll lag nach dem Neustart bis zu 8 s hinter dem Mock (Sperre des
   abgestürzten Workers lief erst ab) → Worker gibt beim Start Sperren frei (`release_stale_leases`); 4 Läufe danach grün.

## Hindernisse

- Kein `pip`/`uv` auf dem Host; Werkzeuge laufen im Container (uv-Image). Docker und Netz standen zur Verfügung.
- KI-Proxy: 2 von 150 Anfragen verbraucht (K6, ein Fehlversuch durch Schemafehler, ein Erfolg), kein 429.

## Phasen

PHASE-1-FERTIG: 2026-11-23T09:11:22Z (Neubau des Images und Regressionslauf nach den letzten Kommentar-Änderungen: 58/58 bestanden, 1 manuell übersprungen). Warte auf `PHASE2.md`.

## Phase 2 (N-1 `appointment.reschedule`)

Beginn 09:25:32Z. Änderung: ein Handler mit `@operation(...)` am Ende von `chronos/domain/appointments.py` (+ Parametermodell,
~20 Zeilen). **Eine Datei, keine weitere Handarbeit**: Endpunkt, `/api/v1/operations`, `/api/v1/ai/tools` und Brückentypen
(`make bridge` erzeugte `AppointmentReschedule{Params,Result}` und den Eintrag in `Operations`) entstanden automatisch;
Rückgängig läuft über die generische Objekttyp-Registry ohne Änderung. Eine Lücke der Operationsbeschreibung gab es nicht
(die Importzeile in `catalog.py` war nicht nötig, da das Modul schon importiert ist). Zusätzlich zu N-1 war die K5-Korrektur
(Schleife 4) an `worker/delivery.py` nötig, unabhängig von der neuen Operation.
Abnahme: Phase 2 2/2, Phase 1 65 Tests ohne Fehler (1 manuell übersprungen).

PHASE-2-FERTIG: 2026-11-23T09:30:00Z

FERTIG: 2026-11-23T09:29:34Z
