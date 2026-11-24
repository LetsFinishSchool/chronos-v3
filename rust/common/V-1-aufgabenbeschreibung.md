# V-1: Aufgabenbeschreibung Spike E-002

Verbindlich für alle drei Kandidaten (TypeScript, Go, Rust). Kriterien und Metriken: `docs/arc42/09-entscheidungen/E-002-spike-kriterien.md`. Diese Datei legt die **Schnittstellen** fest, damit die Abnahmesuite (V-2) sprachunabhängig prüfen kann. Alles, was hier nicht steht, entscheidet der Kandidat.

**Status:** Entwurf. Gegen eine Referenzattrappe (`../reference/`) mit der Abnahmesuite validiert (alle Tests grün außer K6/K3, siehe `acceptance/README.md`).

## 0. Ziel und Rahmen

Gebaut wird ein **minimaler, aber vollständiger Durchstich** von Chronos: Operationsschicht mit einmal beschriebenen Operationen, Team-Baum, Transaktion mit Verlauf und Ereignis, Worker mit Zustellung, Serien (RRULE), Anmeldung über Keycloak, KI-Werkzeugschema, Last, Architekturregel und Frontend-Brücke. Es ist **kein** Produktcode; Funktionen außerhalb dieser Beschreibung werden nicht gebaut.

Rahmenbedingungen: 8 Stunden Wall-Clock, vorgegebene Frameworks, ADR-002 (ein Image, zwei Prozesse `web` und `worker`), ADR-003 (PostgreSQL, gemeinsam genutzt). Keine Geheimnisse im Repository.

## 1. Lieferumfang je Kandidat

Verzeichnis `spikes/e-002/<sprache>/` (`typescript`, `go`, `rust`) mit:

| Datei / Ziel | Inhalt |
|---|---|
| `Dockerfile` | Baut **ein** Image. Build-Kontext ist das Verzeichnis des Kandidaten. Startmodus über das erste Argument: `web` oder `worker`. Läuft als Nicht-Root. Produktionsmodus (Release-Build). |
| `Makefile` | Ziele `build` (Image `chronos-spike-<sprache>`), `test` (eigene Tests), `arch-check` (siehe 9), `bridge` (siehe 10). |
| `README.md` | Ein Absatz zu verwendeten Bibliotheken mit Versionen, Eigenbau-Stellen (mit Dateiangabe), nicht erreichte Aufgaben, Auffälligkeiten. |
| `PROTOKOLL.md` | Ablauf: Zeitstempel je Aufgabe S-1..S-10, Zahl der Korrekturschleifen, Hindernisse. |

Frameworks sind vorgegeben und werden nicht gewechselt: TypeScript Fastify + Kysely + Zod/TypeBox; Go chi + huma + pgx + sqlc; Rust axum + sqlx + serde + utoipa. Bibliotheken für RRULE, Web Push, OIDC, Aufträge, E-Mail und KI-SDK wählt der Kandidat (Auswahl begründen).

## 2. Konfiguration (Umgebungsvariablen)

| Variable | Bedeutung |
|---|---|
| `DATABASE_URL` | PostgreSQL-Verbindung |
| `PORT` | HTTP-Port des Web (Standard 8080); der Worker bietet `GET /healthz` auf `WORKER_HEALTH_PORT` (Standard 8081) |
| `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_REDIRECT_URL` | Keycloak; `OIDC_ISSUER_URL` zeigt auf den Realm |
| `SMTP_HOST`, `SMTP_PORT` | E-Mail, ohne TLS und Anmeldung (Testserver) |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | Web Push |
| `MOCK_CHANNEL_URL` | Mock-Kanal (siehe 6) |
| `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | KI. Der Aufruf geht an `ANTHROPIC_BASE_URL` (Schutz-Proxy mit Grenzen; ohne die Variable an die Anthropic-API), der Schlüssel kommt nur aus der Umgebung. **Kein Streaming** (der Proxy lehnt es ab); nur das Modell `ANTHROPIC_MODEL`; `max_tokens` höchstens 1024. |
| `AI_PRICE_IN_MICRO_EUR_PER_MTOK`, `AI_PRICE_OUT_MICRO_EUR_PER_MTOK`, `EMAIL_PRICE_MICRO_EUR` | Preise für die Kostenerfassung (ganzzahlig, Mikro-Euro) |
| `RETRY_BASE_MS` | Basis der Wiederholung (Standard 1000; Test setzt 200) |
| `STATIC_DIR` | Verzeichnis, das das Web unter `/static/` ausliefert |
| `SPIKE_FAULTS` | `1` aktiviert die Fehlerinjektion (siehe 7) |
| `LOG_FORMAT` | `json` (Standard) |

## 3. Allgemeine API-Regeln

- JSON, UTF-8, `snake_case`. Zeitpunkte: UTC, ISO 8601 mit `Z`, Sekundengenauigkeit (`2026-12-01T17:00:00Z`). IDs: UUID als Zeichenkette (vom Dienst vergeben).
- **Authentifizierung:** `Authorization: Bearer <JWT>` (Keycloak). Prüfen: Signatur über JWKS (`{OIDC_ISSUER_URL}/protocol/openid-connect/certs`), `iss`, `exp`. Person = `sub`; Anzeigename `preferred_username`; E-Mail `email`. Eine Person wird beim ersten authentifizierten Zugriff angelegt oder aktualisiert. Fehlendes oder ungültiges Token: 401.
- **Fehlerformat:** `{"error":{"code":"<snake_case>","message":"<Text>"}}`. Codes: `unauthenticated` 401, `forbidden` 403, `not_found` 404, `validation_error` 422, `invalid_rrule` 422, `conflict` 409, `not_undoable` 409, `provider_error` 502, `internal` 500.
- **Korrelations-ID:** Header `X-Correlation-Id` (≤ 64 Zeichen). Fehlt er, erzeugt der Dienst einen und gibt ihn in der Antwort im selben Header zurück. Die ID gehört in **jeden** Verlaufseintrag, jedes Ereignis, jede Zustellung, jeden Kostenposten und **jede Logzeile** (JSON-Zeilen auf stdout mit Feldern `ts`, `level`, `msg`, `correlation_id`, im Worker auch `event_id`).
- `GET /healthz` (Web und Worker): 200 `{"status":"ok"}`, wenn die Datenbank erreichbar ist.
- Der Web führt beim Start die Datenbankmigrationen aus; der Worker wartet bis zu 60 s auf das Schema.

## 4. Operationsbeschreibung (S-1)

Fachfunktionen gibt es **nur** als Operationen. Jede Operation wird **einmal** beschrieben (Name, Beschreibung, lesend/schreibend, Parameterschema, Ergebnis, Vorschau-fähig). Aus dieser einen Beschreibung entstehen automatisch: Validierung, Endpunkt, `GET /api/v1/operations`, KI-Werkzeugschema und die Typen der Frontend-Brücke. Es darf **keine zweite von Hand gepflegte Liste** geben.

**`GET /api/v1/operations`** (ohne Authentifizierung) liefert:

```json
{"operations":[{"name":"appointment.create","description":"…","mutating":true,"preview_supported":true,
  "params_schema":{ "type":"object","properties":{…},"required":[…],"additionalProperties":false },
  "result_schema":{ "type":"object","properties":{…},"required":[…] }}]}
```
`params_schema` und `result_schema` sind JSON Schema (Draft 2020-12; `result_schema` beschreibt den Inhalt von `result`). Unbekannte oder fehlende Pflichtparameter und falsche Typen ergeben 422 `validation_error`.

**`GET /api/v1/ai/tools`** (ohne Authentifizierung) liefert `{"tools":[{"name","description","input_schema"}]}` im Format der Anthropic-Werkzeugdefinition. Der Name ist der Operationsname mit `_` statt `.` (`appointment_create`); `input_schema` ist gleich `params_schema` der Operation. **Jede** Operation steht darin.

**Aufruf:** `POST /api/v1/operations/{name}` mit `{"params":{…},"preview":false}`.
- Ergebnis: 200 `{"result":{…}}`.
- Schreibende Operation mit `"preview":true`: 200 `{"preview":{"count":<n>,"affected":[{"type":"appointment","id":"<uuid>","change":"<Text>"}]}}` **ohne jede Schreibwirkung** (auch kein Verlaufseintrag, kein Ereignis). Bei lesenden Operationen wird `preview` ignoriert.
- Unbekannte Operation: 404 `not_found`.

## 5. Operationen

„Mitglied“ meint in allen Berechtigungsprüfungen **effektives Mitglied**: direkt Mitglied des Teams **oder eines seiner Unter-Teams** (Mitgliedschaft erbt nach oben). Nicht-Mitglieder erhalten 403 `forbidden` (existiert das Objekt nicht: 404).

| Operation | Art | Parameter | Ergebnis | Regeln |
|---|---|---|---|---|
| `team.create` | schreibend | `name` (1–100), `parent_id`? | `{team_id}` | Der Aufrufer wird direktes Mitglied. Mit `parent_id`: Aufrufer muss Mitglied des Eltern-Teams sein. |
| `team.add_member` | schreibend | `team_id`, `person_id` (Keycloak-`sub`) | `{}` | Aufrufer ist Mitglied. Person muss bekannt sein (hat sich schon angemeldet), sonst 404. Doppeltes Hinzufügen: ohne Wirkung. |
| `team.effective_members` | lesend | `team_id` | `{members:[{person_id,name}]}` | Direkte Mitglieder des Teams **und aller Unter-Teams (beliebig tief)**, ohne Duplikate, nach `person_id` sortiert. |
| `team.effective_teams` | lesend | `person_id`? (Standard: Aufrufer; andere Person: 403) | `{teams:[{team_id,name,parent_id}]}` | Alle Teams mit direkter Mitgliedschaft **und alle übergeordneten Teams**, nach `name`, dann `team_id` sortiert. |
| `appointment.create` | schreibend | `team_id`, `title` (1–200), `starts_at`, `ends_at` (nach `starts_at`), `timezone` (IANA-Name) | `{appointment_id}` | Status `geplant`. Verlauf (`action` `appointment.create`), Ereignis `appointment.created`, Empfänger = alle effektiven Mitglieder **außer dem Aufrufer**. |
| `appointment.get` | lesend | `appointment_id` | `{appointment:{id,team_id,title,starts_at,ends_at,timezone,status}}` | Status: `geplant`, `abgesagt`, `gelöscht` (gelöschte sind per `get` nicht abrufbar: 404). |
| `appointment.list` | lesend | `team_id` | `{appointments:[…wie get…]}` | Inklusive `abgesagt`, ohne `gelöscht`; nach `starts_at`, dann `id` sortiert. |
| `appointment.cancel` | schreibend, Vorschau | `appointment_id` | `{}` | `geplant` → `abgesagt`. Bereits abgesagt: 409 `conflict`. Verlauf, Ereignis `appointment.cancelled`, Empfänger wie oben. |
| `history.list` | lesend | `object_id`?, `limit`? (1–200, Standard 50) | `{entries:[…]}` | Neueste zuerst; nur Objekte in Teams, in denen der Aufrufer Mitglied ist. Eintrag: `id`, `at`, `actor`, `action`, `object_type`, `object_id`, `before`, `after`, `bundle_id`, `correlation_id`, `undone`, `undo_of`. `before`/`after` sind vollständige Zustandsabbilder des Objekts (`null` bei Anlage bzw. nicht vorhanden). |
| `history.undo` | schreibend, Vorschau | `history_id` | `{history_id}` (der neue Eintrag) | Stellt `before` wieder her (bei `appointment.create`: Status `gelöscht`). Nur zulässig, wenn der aktuelle Zustand des Objekts gleich `after` des Eintrags ist, sonst 409 `not_undoable` mit Grund in `message`. Markiert den Eintrag `undone=true`; schreibt einen neuen Eintrag `action` `history.undo` mit `undo_of`. Ein Rückgängig lässt sich selbst rückgängig machen. Ereignis `change.reverted` mit den Empfängern des ursprünglichen Ereignisses. |
| `series.create` | schreibend | `team_id`, `title`, `rrule`, `dtstart` (Ortszeit `2026-03-02T18:00:00`), `timezone`, `duration_minutes` (1–1440), `exdates`? (Ortszeiten) | `{series_id}` | `rrule` **ohne** Präfix `RRULE:`. Ungültige RRULE: 422 `invalid_rrule`. Verlaufseintrag; kein Ereignis. |
| `series.occurrences` | lesend | `series_id`, `from`, `to` (UTC) | `{occurrences:[{starts_at,ends_at}]}` | `from` eingeschlossen, `to` ausgeschlossen; höchstens 1000; nach `starts_at` sortiert. Wanduhrsemantik: Die Ortszeit bleibt über Sommerzeitwechsel gleich, Ausgabe in UTC. `exdates` entfernen Vorkommen. Ob Vorkommen gespeichert oder berechnet werden, entscheidet der Kandidat. |
| `notification.set_channels` | schreibend | `channels` (nicht leere, geordnete Liste aus `mock`, `email`, `webpush`) | `{}` | Einstellung des Aufrufers. Standard einer neuen Person: `["webpush","email"]`. |
| `notification.subscribe_push` | schreibend | `endpoint` (https-URL), `p256dh`, `auth` | `{}` | Speichert ein Web-Push-Abo des Aufrufers. |
| `notification.test_push` | schreibend | – | `{event_id}` | Erzeugt Ereignis `notification.test` nur für den Aufrufer, zugestellt **ausschließlich** über `webpush` (unabhängig von der Kanaleinstellung). Für den manuellen Test K3. |
| `notification.list` | lesend | `event_id`?, `correlation_id`?, `limit`? (1–500, Standard 100) | `{deliveries:[…]}` | Zustellprotokoll: Zustellungen von Ereignissen, die der Aufrufer **ausgelöst** hat oder bei denen er **Empfänger** ist; älteste zuerst. Eintrag: `event_id`, `event_type`, `correlation_id`, `trigger:{kind,actor}`, `recipient`, `channel`, `attempt`, `result` (`success`, `failed`, `skipped`), `error`?, `at`, `idempotency_key`. Je **Versuch** eine Zeile. |
| `cost.list` | lesend | `limit`? | `{entries:[…]}` | Kostenposten des Aufrufers (als Verursacher). Eintrag: `id`, `at`, `person_id`, `provider` (`anthropic`, `smtp`), `trigger:{kind,name,correlation_id}`, `quantity`, `amount_micro_eur`. |
| `ai.ask` | lesend* | `prompt`, `team_id`? | `{text,proposed_calls:[{name,input}],usage:{input_tokens,output_tokens}}` | Ruft die Anthropic-Messages-API mit den Werkzeugen aus `/api/v1/ai/tools` (`max_tokens` 1024, Zeitlimit 60 s). Führt vorgeschlagene Aufrufe **nicht aus**. `proposed_calls[].name` ist der Operationsname mit Punkt. Zugesicherte Kostenerfassung: ein Posten `provider` `anthropic` mit `quantity` `{input_tokens,output_tokens}`. Anbieterfehler: 502 `provider_error`. |

\* „lesend“, weil `ai.ask` selbst nichts in Chronos verändert.

### Ereignisse, Verlauf, Zustellung (S-3, S-4)

- **Eine Transaktion:** Zustandsänderung, Verlaufseintrag **und** Ereignis (mit allen Empfängern) werden in **derselben** Datenbanktransaktion geschrieben. Scheitert eines, bleibt nichts zurück.
- **Ereignis:** Typ, `trigger` (`{"kind":"person","actor":"<sub>"}`), Korrelations-ID, Empfängerliste.
- **Asynchron:** Die Operation antwortet, **bevor** zugestellt wird. Der **Worker** liest festgehaltene Ereignisse aus der Datenbank (kein direkter Aufruf vom Web) und stellt zu. Der Weg zwischen Web und Worker ist Sache des Kandidaten, aber ausschließlich über die Datenbank.
- **Zustellung je Empfänger:** Kanäle der Reihe nach laut `notification.set_channels`. Je Kanal bis zu **3 Versuche** (Wartezeit `RETRY_BASE_MS`, dann ×2). Schlagen alle Versuche fehl, folgt der **nächste Kanal** der Liste (Ersatzkanal). Scheitern alle Kanäle: letzte Zeile `result=failed`. Hat der Empfänger für einen Kanal keine Voraussetzung (kein Push-Abo): Zeile `result=skipped`, weiter zum nächsten Kanal.
- **Idempotenzschlüssel:** `<event_id>:<recipient>:<channel>`. Er wird jeder Zustellung mitgegeben (siehe Kanäle) und in `notification.list` ausgewiesen.
- **Kostenposten:** Jede **erfolgreiche** E-Mail-Zustellung erzeugt einen Kostenposten `provider=smtp`, `quantity={"messages":1}`, `amount_micro_eur=EMAIL_PRICE_MICRO_EUR`, Verursacher: Auslöser des Ereignisses, Auslöser `kind=operation` mit Name und Korrelations-ID.
- **Wiederanlauf:** Wird der Worker mit `SIGKILL` beendet und neu gestartet, setzt er unfertige Zustellungen fort. **Kein Ereignis darf verloren gehen.** Doppelte Versuche sind zulässig, sofern der Idempotenzschlüssel gleich bleibt; sie werden gezählt (siehe K5/M-14).

### Kanäle

| Kanal | Verhalten |
|---|---|
| `mock` | `POST {MOCK_CHANNEL_URL}/deliver` mit JSON `{"recipient","event_type","event_id","correlation_id"}` und Header `Idempotency-Key`. 2xx = Erfolg, sonst Fehler. Der Mock braucht je Aufruf 50 ms und lässt sich für Empfänger fehlschlagen (siehe V-4). |
| `email` | SMTP an `SMTP_HOST:SMTP_PORT`; `From: chronos-spike@example.test`; `To`: E-Mail der Person aus dem Token; Betreff enthält den Ereignistyp; Header `X-Chronos-Idempotency-Key` und `X-Chronos-Correlation-Id`. |
| `webpush` | Web Push (VAPID, verschlüsselte Nutzlast) an alle Abos der Person; Nutzlast JSON `{"event_type","event_id"}`. Ohne Abo: `skipped`. |

## 6. Mock-Kanal (Bestandteil von V-4, hier nur die Schnittstelle)

`POST /deliver` (Verhalten wie oben; wiederholter `Idempotency-Key` ergibt 200 mit `{"duplicate":true}`), `POST /control` mit `{"fail_for":["<recipient>"],"latency_ms":50}`, `GET /stats` mit `{"effective":n,"duplicates":m,"keys":{"<key>":<anzahl der angenommenen Aufrufe>},"deliveries":[{"key","recipient","correlation_id"}]}` (`deliveries` enthält jede wirksame Zustellung genau einmal), `POST /reset`.

## 7. Fehlerinjektion

Nur mit `SPIKE_FAULTS=1`: Trägt eine Anfrage den Header `X-Spike-Fault: after_history`, wirft der Dienst **nach** dem Schreiben des Verlaufseintrags und **vor** dem Schreiben des Ereignisses einen Fehler (500 `internal`). Wegen der gemeinsamen Transaktion darf **nichts** davon bestehen bleiben (Objekt, Verlauf, Ereignis). Ohne `SPIKE_FAULTS=1` wird der Header ignoriert.

## 8. Anmeldung (S-6)

- `GET /auth/login`: 302 zum Keycloak-Autorisierungsendpunkt, Authorization Code mit **PKCE (S256)** und `state`.
- `GET /auth/callback?code=…&state=…`: tauscht den Code, prüft `state`, setzt das Cookie `chronos_session` (`HttpOnly`, `SameSite=Lax`, `Path=/`), 302 nach `/`. Fehlerhafter `state`: 400.
- `GET /auth/me`: gültiges Cookie **oder** Bearer-Token → 200 `{"person_id","name","email"}`, sonst 401.
- `POST /auth/logout`: 204, Cookie wird gelöscht, die Sitzung ist **serverseitig ungültig** (ein zuvor kopiertes Cookie liefert danach 401 bei `/auth/me`).
- Chronos speichert keine Passwörter und implementiert Token-Prüfung und OIDC-Fluss **nicht selbst** (Bibliothek).

## 9. Architekturregel (S-9)

Fachbereiche und Kanäle sind getrennte Module. Regel: **Das Modul der Fachbereiche (Teams, Termine, Serien, Verlauf) darf das Modul der Kanäle (`mock`, `email`, `webpush`) nicht kennen** (weder importieren noch davon abhängen). Der Kandidat prüft das automatisch: `make arch-check` endet mit Exit-Code 0, wenn die Regel eingehalten ist, und ≠ 0 bei Verstoß. Bei der Auswertung wird ein Verstoß gezielt eingebaut und die Dauer bis zur Meldung gemessen.

## 10. Frontend-Brücke (S-10)

Aus der Operationsbeschreibung entstehen **typisierte Aufrufe** für einen TypeScript-Client.
- `make bridge` erzeugt in `bridge/generated/` Typen (und ggf. Aufrufhilfen) aus `GET $BASE_URL/api/v1/operations` (der Dienst läuft dabei).
- `bridge/client.ts` exportiert `createClient(baseUrl: string, getToken: () => string)`. Der Client hat eine Methode `call(name, params)`, deren Typ **vom Operationsnamen abhängt**: `params` und das Ergebnis (`Promise<…>`) sind die aus `params_schema` bzw. `result_schema` erzeugten Typen; ein unbekannter Name ist ein Übersetzungsfehler. `bridge/tsconfig.json` ist `strict`, `include` deckt alle `*.ts` im Verzeichnis `bridge/` ab.
- Die Prüfung (Dateien im Verzeichnis `spikes/e-002/common/bridge-check/`, vom Prüfer hinzugefügt): `good.ts` (korrekter Aufruf, Ergebnis als `string` verwendet) übersetzt fehlerfrei; `bad-param-type.ts` (`title: 42`), `bad-missing-param.ts` und `bad-unknown-op.ts` lassen den Übersetzungslauf jeweils scheitern.
- Für TypeScript-Kandidaten darf die Brücke über gemeinsam genutzte Schemata laufen; für Go und Rust ist Codegenerierung zulässig. Wie viel von Hand getippt werden muss, fließt in Q-5 ein.

## 11. Nachtrag N-1 (Phase 2, erst nach Abschluss von Phase 1 freigegeben)

Der Agent erhält nach Phase 1 die Zusatzaufgabe: Operation **`appointment.reschedule`** ergänzen: Parameter `appointment_id`, `starts_at`, `ends_at`; schreibend, Vorschau; Verlaufseintrag; Ereignis `appointment.rescheduled` mit den Empfängern wie bei `appointment.create`. Es dürfen **keine** weiteren Änderungen an Endpunkten, Werkzeuglisten, Brückentypen oder Dokumentation von Hand nötig sein. Gemessen wird M-11: berührte Dateien/Module, und ob die Operation ohne Zusatzaufwand in `/api/v1/operations`, `/api/v1/ai/tools` und in den Brückentypen erscheint.

## 12. Nicht-Ziele

Keine Oberfläche außer den Dateien in `STATIC_DIR`, keine weiteren Fachfunktionen, keine Mehrsprachigkeit, keine Berechtigungsrollen, kein Löschen nach 30 Tagen, keine Bündelung der Benachrichtigungen, keine Datenübernahme, keine Beobachtungswerkzeuge außer den JSON-Logs.
