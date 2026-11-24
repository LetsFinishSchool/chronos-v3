# Spike E-002, Kandidat python

Durchstich von Chronos in Python 3.13 mit FastAPI, Pydantic v2, SQLAlchemy 2 (asynchron, psycopg 3), Start mit uvicorn
(`web` und `worker`, je ein Prozess). Ein Image `chronos-spike-python`, mehrstufiger Build (uv-Image → `python:3.13-slim`),
Nicht-Root, Abhängigkeiten über `uv.lock` gesperrt. Ziele: `make build | test | arch-check | bridge`.

## Aufbau (eine Beschreibung je Operation)

- `chronos/ops/registry.py`: `@operation(name, beschreibung, mutating, preview)` an einer Funktion `handler(ctx, p: P) -> R`;
  P und R sind Pydantic-Modelle. Daraus entstehen Validierung, Endpunkt (`POST /api/v1/operations/{name}`),
  `GET /api/v1/operations`, `GET /api/v1/ai/tools`, das KI-Werkzeugschema in `ai.ask` und die Brückentypen. Es gibt keine
  zweite Liste; eine neue Operation = ein Modul mit `@operation` + eine Importzeile in `chronos/catalog.py`.
- Vorschau: dieselbe Handlerlogik läuft in der Transaktion und wird per Rollback verworfen; `affected` stammt aus den
  geschriebenen Verlaufseinträgen. Dadurch gibt es keine zweite „Vorschau“-Implementierung je Operation.
- Verlauf/Rückgängig (`chronos/core/history.py`) ist über eine Objekttyp-Registry generisch (Zustandsabbild laden/speichern).
- Module: `chronos.core` (Kontext, Zugriff, Ereignisse, Verlauf), `chronos.domain` (Teams, Termine, Serien, Verlaufs-
  operationen), `chronos.notifications`, `chronos.ai`, `chronos.channels` (mock, email, webpush), `chronos.worker`, `chronos.web`.
- Architekturregel S-9: `import-linter` (Vertrag „forbidden“ in `pyproject.toml`): `chronos.domain` und `chronos.core`
  dürfen `chronos.channels` weder direkt noch indirekt importieren. Verstoß gezielt getestet: `make arch-check` endet mit Exit 2.
- Zustellung: Ereignis + je Empfänger eine Zeile in `delivery_task` (gleiche Transaktion wie Zustand und Verlauf). Der Worker
  holt fällige Zeilen mit `FOR UPDATE SKIP LOCKED` und setzt eine Sperre (`lease_until`, 8 s); Fortschritt (Kanalindex,
  Versuch, nächster Zeitpunkt) wird zusammen mit der Zustellzeile in einer Transaktion geschrieben. Nach `SIGKILL` läuft die
  Sperre ab, ein neuer Worker setzt fort (gleicher Idempotenzschlüssel).
- Brücke: `bridge/generate.py` holt `/api/v1/operations`, erzeugt je Operation Typen mit `json-schema-to-typescript` und
  `generated/operations.ts` (Abbildung Name → {params, result}). Von Hand getippt: `bridge/client.ts` (25 Zeilen, generisch
  über `keyof Operations`), `bridge/tsconfig.json` und das Skript (56 Zeilen). Typen je Operation: 0 Zeilen von Hand.

## Bibliotheken (Version laut `uv.lock`)

| Zweck | Bibliothek |
|---|---|
| Web | fastapi 0.165.0, uvicorn[standard] 0.54.0 (uvloop 0.23.0), pydantic 2.14.4 |
| Datenbank | sqlalchemy 2.1.9 (asyncio), psycopg 3.3.9 (binary, pool); PostgreSQL 17 |
| RRULE | python-dateutil 4.0.0 (`rrulestr`), tzdata 2026.6, `zoneinfo` |
| Token-Prüfung (JWKS) | pyjwt 2.15.1 (+ cryptography 50.0.2) |
| OIDC-Code-Flow mit PKCE | authlib 1.9.10 (AsyncOAuth2Client) + httpx 0.28.1 |
| Web Push (VAPID, Verschlüsselung) | pywebpush 2.5.0 (py-vapid 1.9.6, http-ece) – kein eigener Kryptocode |
| E-Mail | aiosmtplib 5.1.3 |
| KI | anthropic 2.12.0 (AsyncAnthropic mit `base_url` = Schutz-Proxy) |
| Aufträge | keine Bibliothek: eigene Warteschlange auf PostgreSQL (siehe Eigenbau) |
| Architekturregel | import-linter 2.17 |
| Tests | pytest 9.2.0; Abnahmesuite aus `common/acceptance` |
| Brücke | json-schema-to-typescript 15.0.4 (npx), typescript 5.6 (Prüfung) |

## Eigenbau (`EIGENBAU:BEGIN/END`)

| Datei | Zweck |
|---|---|
| `chronos/domain/series.py` | Zusatzprüfung der RRULE (dateutil lässt COUNT+UNTIL, INTERVAL=0, BYMONTHDAY=0, fehlendes FREQ durch); ~15 Zeilen. Die Ausdehnung selbst macht dateutil. |
| `chronos/worker/delivery.py` | Auftragswarteschlange (Abholen mit SKIP LOCKED, Sperre, Wiederholung/Ersatzkanal, Schleife); ~100 Zeilen. Statt Auftragsbibliothek, weil Fortschritt je Empfänger/Kanal und Wiederanlauf fachlich eng sind. |
| `chronos/ops/registry.py` | JSON-Schema-Nachbearbeitung (`$ref` auflösen, `title` entfernen, `X \| None` bei optionalen Parametern vereinfachen); ~30 Zeilen. |
| `chronos/db.py` | Migrationsläufer für `schema.sql` (Advisory-Lock, idempotentes SQL); statt Alembic. |

Kein Eigenbau bei Kryptografie, Token-Prüfung, OIDC, Web Push.

## Annahmen

- Das Arbeitsverzeichnis ist `python/` im Repository-Ordner; `common/` liegt eine Ebene darüber (`../common`).
- `team.create`/`team.add_member` schreiben keinen Verlauf (V-1 verlangt ihn nur für Termine und Serien).
- `history.list` ohne `object_id` liefert Einträge aller Teams, in denen der Aufrufer effektiv Mitglied ist.
- `history.undo`: bereits rückgängig gemachte Einträge → 409 `not_undoable`. `change.reverted` geht an die Empfänger des
  ursprünglichen Ereignisses; hatte der Eintrag kein Ereignis (z. B. `series.create`), gibt es keins.
- Vorschau für schreibende Operationen ohne Vorschau-Unterstützung → 422 `validation_error`.
- `notification.list`: bei Überschreiten von `limit` werden die neuesten Zeilen geliefert, aufsteigend sortiert.
- `notification.test_push` setzt `payload.channels=["webpush"]` am Ereignis; der Worker bevorzugt diese Liste.
- Eine Person ohne E-Mail-Adresse → E-Mail-Kanal `skipped`. Mehrere Push-Abos: Erfolg, wenn mindestens eines ankommt.
- Optionale Parameter erscheinen im Schema als einfacher Typ (nicht Pflicht), nicht als `anyOf` mit `null`.
- Unbekannte Operation wird vor der Authentifizierung mit 404 beantwortet.
- Der Worker geht von einem Prozess aus: beim Start gibt er alle Sperren frei (schneller Wiederanlauf nach SIGKILL). Mehrere Worker blieben durch SKIP LOCKED korrekt, nur mit zusätzlichen Doppelversuchen.
- `ai.ask` hält die Transaktion während des KI-Aufrufs offen (kurze Last, 60 s Zeitlimit).

Widersprüche zwischen V-1 und Tests: keine gefunden.

## Nicht erreichte Aufgaben

Keine in Phase 1. K3 (Web Push im Browser) ist manuell und nicht getestet; geprüft wurde nur, dass `/static/` ausgeliefert wird,
`/api/v1/push/vapid-public-key` den Schlüssel liefert, der VAPID-Schlüssel mit pywebpush lädt und eine Zustellung an einen
unerreichbaren Endpunkt verschlüsselt/signiert und sauber als `failed` protokolliert wird. S-8 (Last) nur als Selbstkontrolle:
16 parallele Clients, 20 s, 1048 Anfragen (Anlegen + Liste), keine Fehler, p99 0,54 s, Web ~130 MiB, Worker ~77 MiB.

## Abnahme (Phase 1, eigener Lauf)

65 Tests, alle bestanden, 1 übersprungen (manuell: Fehlerinjektion ohne `SPIKE_FAULTS`). K5: 32 von 200 Zustellungen beim
Abbruch wirksam, 0–14 Duplikat-Versuche (vom Mock abgefangen). K6 bestand beim ersten echten Lauf nach Behebung eines Fehlers (s. u.).

## Auffälligkeiten

- Python-Bibliotheken waren durchweg reif und passten ohne Umwege: **RRULE** (dateutil) deckt den ganzen Katalog ab, braucht nur
  die vier Zusatzprüfungen; die Golden-Datei stammt aus dateutil, das Ergebnis ist also kein unabhängiger Beleg.
  **OIDC** (authlib: PKCE, State) und **JWKS-Prüfung** (PyJWT; `PyJWKClient` ist synchron, läuft in `asyncio.to_thread`, ohne
  Begrenzung bei unbekannter `kid`) ohne Probleme. **Web Push** (pywebpush) ist synchron (`requests`), läuft in einem
  Thread; `Vapid.from_raw` für den rohen Schlüssel aus `gen_vapid.py` nötig. **KI-SDK** (anthropic): `base_url` für den Proxy
  genügt; `max_retries=0`, um das Anfragebudget des Proxys nicht zu verbrauchen. **Aufträge**: keine Bibliothek gewählt.
- Fehler beim Bauen: Meine Schema-Nachbearbeitung entfernte zunächst jeden Schlüssel `title`, auch das Feld `title` von
  `appointment.create` (K6 meldete es). Behoben, durch Unit-Test abgesichert.
- `uv` lokal nicht vorhanden: `make test|arch-check|lock` nutzen das uv-Image per Docker, wenn `uv` fehlt.
- Container-uv legte `uv.lock` zunächst als root an (Schreibrechte); seither läuft der Container mit der Benutzer-ID.

## Phase 2

`appointment.reschedule` (N-1): eine Datei geändert (`chronos/domain/appointments.py`), alles Weitere (Endpunkt, Operationsliste, KI-Werkzeuge, Brückentypen, Rückgängig) automatisch. Phase 2: 2/2, Phase 1 weiter fehlerfrei.
