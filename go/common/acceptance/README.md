# V-2: Abnahmesuite (HTTP-Blackbox)

Sprachunabhängige Prüfung der drei Spike-Kandidaten gegen die Schnittstellen aus `../V-1-aufgabenbeschreibung.md`. Nur Python-Standardbibliothek (Python ≥ 3.10), keine Installation nötig.

**Status:** Gegen die Referenzattrappe (`../../reference/`, Python mit PostgreSQL) und die Umgebung aus `../env/` validiert: alle Tests grün (Phase 1: 61 von 62 ausführbaren, 1 manuell übersprungen; Phase 2: 2 von 2). **K6** (echter KI-Aufruf) ist mit Schlüssel gegen die Attrappe bestanden. **Nicht validiert:** K3 (Web Push, manuell). Die Validierung hat Fehler in der Attrappe und in vier Tests aufgedeckt (siehe „Erkenntnisse“); sie belegt, dass Vertrag und Tests zusammenpassen, nicht, dass ein Kandidat sie besteht.

## Voraussetzungen (V-4, vorhanden in `../env/`)

Laufende Umgebung: Kandidat (`web`, `worker`), PostgreSQL, Keycloak mit Realm `chronos-spike` (Clients `chronos-spike-test` mit Direct Grant und `chronos-spike-web`; Benutzer `alice`, `bob`, `carol` mit E-Mail `<name>@example.test`, Passwort `spike-pass`), Mailpit, Mock-Kanal, `SPIKE_FAULTS=1`, `RETRY_BASE_MS=200`. Start: `../env/stack.sh up <name> <offset> <image>`, Variablen: `eval "$(../env/stack.sh env <name> <offset>)"`.

## Aufruf

```sh
export BASE_URL=http://localhost:8080 KEYCLOAK_URL=http://localhost:8180 MAILPIT_URL=http://localhost:8025 MOCK_URL=http://localhost:8090
export COMPOSE="docker compose -p chronos-spike-ts -f /pfad/zu/compose.yaml"   # für K5 und M-15 (Worker beenden, Logs)
export CANDIDATE_DIR=/pfad/zu/spikes/e-002/typescript                          # für S-10
python3 run_acceptance.py --json bericht.json          # Phase 1
python3 run_acceptance.py --phase 2 --json n1.json     # Phase 2 (N-1), erst nach der Zusatzaufgabe
python3 run_acceptance.py --only K2,K4                 # Auswahl
```
`SKIP_AI=1` überspringt K6 (ohne Anthropic-Zugang). `TSC` setzt den TypeScript-Compiler (Standard: `npx --yes -p typescript@5.6 tsc`, braucht Netz). Der Bericht zeigt je Kennzeichnung die Zahl bestandener Tests.

## Zuordnung zu den Kriterien

| Tag | Datei | Prüft |
|---|---|---|
| S1 | `test_s1_operations.py` | Operationsbeschreibung, Werkzeugliste, Validierung, Vorschau ohne Wirkung, Korrelations-ID |
| S2 | `test_s2_team_tree.py` | Team-Baum, Vererbung nach oben, Berechtigung |
| S3 | `test_s3_transaction.py` | Verlauf, Ereignis, Rückgängig, Atomarität bei Fehler |
| K2 | `test_s5_rrule.py` + `golden/` | RRULE: 21 gültige Fälle (davon Sommerzeit, `BYSETPOS`, `WKST`, `EXDATE`, Fenster), 6 ungültige, Limit 1000 |
| K4 | `test_s6_auth.py` | Bearer-Prüfung, OIDC-Code-Flow mit PKCE (skriptgesteuert), Abmeldung |
| K5 | `test_s4b_crash.py` | `SIGKILL` des Workers mit 200 Zustellungen im Rückstau |
| K6 | `test_s7_ai.py` | Echter KI-Aufruf, Werkzeugschema, Kostenposten |
| M14 | `test_s4_worker.py` | Wiederholung, Ersatzkanal, Überspringen, Endgültig fehlgeschlagen, Asynchronität, Gesundheitsprüfung |
| M15 | `test_s4_worker.py` | Korrelations-ID in den Logs von Web und Worker |
| S10 | `test_s10_bridge.py` + `../bridge-check/` | Typisierter Client: gute Aufrufe übersetzen, schlechte nicht |
| N1 | `test_n1_reschedule.py` | Neue Operation `appointment.reschedule` (Phase 2) |

**Nicht Teil dieser Suite:** K1 (Budget, kommt mit V-3), K3 (Web Push, manuell: `manual/K3-webpush.md`), K7 (Image-Build und Start, V-4), K2-Regel „Eigenbau höchstens 100 Zeilen“ (Durchsicht), M-12 Architekturverstoß (V-3, manuell), M-8/M-9 (Werkzeuge der Sprache).

## Erkenntnisse aus der Validierung

1. **Mailpit-API** (`/api/v1/search`, `/api/v1/message/<id>/headers`) wie angenommen. E-Mail-Kopfzeilen werden von Bibliotheken unterschiedlich kodiert (RFC 2047); der Test dekodiert sie vor dem Vergleich.
2. **Keycloak-Anmeldeformular** (`kc-form-login`) wie angenommen. Keycloak setzt `Secure`-Cookies; Browser behandeln `http://localhost` als sicher, Python nicht, daher lässt der Test Secure-Cookies über HTTP zu.
3. **Rootless Docker** (Fedora): Dateien, die in Container gemountet werden, müssen für den Containerbenutzer lesbar sein (Realm-Datei mit 644). `network_mode: host` ist von außen erreichbar.
4. **Mock-Kanal** nach V-1 §6 (in `../env/mock-channel/`); `keys` zählt angenommene Aufrufe.
5. **K5-Ergebnis der Attrappe:** Beim Abbruch waren 16 von 200 Zustellungen wirksam; nach Neustart kamen alle an, 4 Duplikat-Versuche wurden vom Mock abgefangen.
5. **K5-Semantik:** Exakt-einmal gibt es bei externen Kanälen nicht. Der Test verlangt: **kein Verlust**, jede (Korrelations-ID, Empfänger)-Zustellung **wirksam genau einmal** (der Mock dedupliziert nach `Idempotency-Key`); Duplikat-Versuche werden **gezählt und berichtet**, nicht als Fehler gewertet.

## Golden-Datei

`golden/rrule_cases.json` wurde mit `golden/generate_rrule_golden.py` (python-dateutil als Referenz, Wanduhrsemantik in Europe/Berlin) erzeugt und stichprobenartig von Hand geprüft (Sommerzeit-Wechsel, Schaltjahr, `BYSETPOS`, `WKST`, `UNTIL`, Jahrestage, KW). Nicht enthalten: untertägige Frequenzen und nicht existierende Ortszeiten (uneinheitliche Semantik).
