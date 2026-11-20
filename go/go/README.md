# Spike E-002, Kandidat Go

Ein Go-Programm (`cmd/chronos`), zwei Startarten `web` und `worker`, ein mehrstufiges Image (`golang:1.27-alpine` → `distroless/static:nonroot`, statisch gelinkt, 32,6 MB). Stand: Phase 1 vollständig, alle ausführbaren Tests der Abnahmesuite grün (65 Tests, 1 manuell übersprungen).

## Aufbau (eine Beschreibung je Operation)

Jede Operation wird genau einmal mit `op.Register(reg, op.Op{Name, Description, Mutating}, handler)` beschrieben; Parameter- und Ergebnistyp sind die Go-Typen des Handlers (mit `json`-/huma-Tags). Daraus entstehen automatisch: Validierung und Endpunkt (huma, ein `POST /api/v1/operations/<name>` je Operation), `GET /api/v1/operations`, `GET /api/v1/ai/tools`, das KI-Werkzeugschema in `ai.ask` und die Typen der Frontend-Brücke (`make bridge`). Eine Operation hinzuzufügen heißt, eine `op.Register`-Gruppe in einer Datei zu ergänzen.

- `internal/op`: Registry, Transaktion (schreibend = eine Transaktion; Vorschau = ausführen und zurückrollen), Verlauf/Ereignis (`Ctx.Record`, `Ctx.Emit`), Fehlerformat, Korrelations-ID, Zugriffslog.
- `internal/domain`: Teams, Termine, Serien, Verlauf (kennt die Kanäle nicht, `make arch-check`).
- `internal/notify`, `internal/ai`: Operationen für Benachrichtigung/Kosten und KI.
- `internal/channels` + `internal/worker`: Kanäle `mock`/`email`/`webpush` und der Worker (liest nur aus der Datenbank).
- `internal/auth`: Bearer-Prüfung und OIDC-Code-Flow (PKCE) mit serverseitiger Sitzung.
- `internal/db`: goose-Migrationen (`migrations/`), sqlc-Abfragen (`queries/`, erzeugter Code in `sqlc/` ist eingecheckt; `make generate`).
- `bridge/`: `gen.mjs` (erzeugt `generated/operations.ts` aus `/api/v1/operations`), `client.ts` (generischer Client, ca. 20 Zeilen, ohne Operationsliste).

## Verwendete Bibliotheken (Version)

| Zweck | Bibliothek | Version |
|---|---|---|
| Router (vorgegeben) | go-chi/chi/v5 | v5.5.0 |
| Operationsbeschreibung/Validierung (vorgegeben) | danielgtaylor/huma/v2 | v2.41.0 |
| Datenbank (vorgegeben) | jackc/pgx/v5 | v5.13.0 |
| SQL-Erzeugung (vorgegeben) | sqlc | v1.31.1 |
| Migrationen | pressly/goose/v3 | v3.30.1 |
| RRULE | teambition/rrule-go | v1.8.2 |
| OIDC/JWT | coreos/go-oidc/v3 (mit go-jose v4.1.9), golang.org/x/oauth2 | v3.21.0, v0.38.0 |
| Web Push | SherClockHolmes/webpush-go | v1.4.0 |
| E-Mail | wneessen/go-mail | v0.8.2 |
| KI-SDK | anthropics/anthropic-sdk-go | v1.84.0 |
| UUID | google/uuid | v1.6.0 |
| Brücke (Node) | json-schema-to-typescript | 15.0.4 |

Aufträge: bewusst **keine** Bibliothek (River lag im Modul-Cache vor); siehe Eigenbau.

## Eigenbau (mit `EIGENBAU:BEGIN/END` markiert)

| Datei | Zweck | Umfang |
|---|---|---|
| `internal/domain/series.go` | Wanduhr-Ausdehnung der RRULE um rrule-go: Ortszeit als schwebende Zeit, UNTIL (UTC) in Ortszeit, EXDATE, Fenster, Obergrenze 1000; zusätzliche Gültigkeitsprüfungen (COUNT+UNTIL, INTERVAL<1, BYMONTHDAY=0, FREQ fehlt), die rrule-go nicht ablehnt | ca. 90 Zeilen |
| `internal/worker/worker.go` | Auftragsschleife (Outbox-Tabelle `event_recipients`, `FOR UPDATE SKIP LOCKED`, Wiederholung je Kanal, Ersatzkanal, Wiederaufnahme aus den Zeilen in `deliveries`) | ca. 130 Zeilen |
| `internal/op/registry.go` | Auflösen der `$ref` im huma-Schema, damit `params_schema`/`result_schema` in sich geschlossen sind | ca. 45 Zeilen |

Kein eigenes Kryptografie-, Token- oder OIDC-Stück. Nicht markiert, aber Skript-Klebstoff: `make arch-check` (`go list -test -deps` plus `grep`) und `bridge/gen.mjs`.

## Annahmen

- Vorschau (`preview:true`) gilt für **alle** schreibenden Operationen: Der Handler läuft in der Transaktion, die danach zurückgerollt wird; `affected` melden die Handler über `Ctx.Affect`. Deshalb ist `preview_supported` = `mutating`. Fehler (z. B. 409) erscheinen in der Vorschau wie in der echten Ausführung.
- `appointment.get`/`list`, `series.occurrences`, `history.undo` prüfen erst Existenz (404), dann Mitgliedschaft (403). `history.list` filtert nicht sichtbare Objekte still heraus.
- `bundle_id` ist je Operationsaufruf eine neue UUID (der Test verlangt einen Wert).
- Rückgängig: Ein bereits rückgängig gemachter Eintrag ist `not_undoable`. Wird ein `history.undo` selbst rückgängig gemacht, wird `undone` des ursprünglichen Eintrags wieder `false`. Rückgängig ist nur für Termine implementiert (Serien: `not_undoable`).
- Verlauf gibt es nur für Termine und Serien (Teams und Einstellungen haben keinen Verlauf; nicht verlangt).
- Ereignis `change.reverted` geht an die Empfänger des ursprünglichen Ereignisses (aus `event_recipients`).
- `team.create`/`add_member` erzeugen kein Ereignis. `notification.test_push` setzt `events.forced_channel = webpush`.
- Gelöschte Termine bleiben mit Status `gelöscht` in der Tabelle (für Rückgängig des Rückgängig).
- Sitzungscookie ohne `Secure` (Test über HTTP); die Sitzung steht in der Tabelle `sessions`. `state` und PKCE-Verifier stehen in `auth_flows` (10 Minuten, einmalig). Das Cookie gilt nur für `/auth/me`, Operationen verlangen ein Bearer-Token.
- Bearer-Prüfung prüft Signatur (JWKS aus der Discovery), `iss`, `exp`; die Zielgruppe (`aud`) wird nicht geprüft (Keycloak-Access-Token tragen `account`).
- Der Worker setzt beim Start alle Beanspruchungen zurück (ein Worker-Prozess wird vorausgesetzt); zusätzlich läuft eine Beanspruchung nach 120 s ab. Doppelte Versuche nach SIGKILL tragen denselben Idempotenzschlüssel.
- Web Push gilt als erfolgreich, wenn mindestens ein Abo den Push annimmt. Nicht geprüft (K3 ist manuell).
- Ungültige JSON-Syntax und Validierungsfehler ergeben 422 `validation_error` (huma meldet 400 → umgeleitet).
- `ai.ask` prüft bei angegebenem `team_id` die Mitgliedschaft; Kosten = `(in·Preis_in + out·Preis_out + 500000) / 1e6` (gerundet, ganzzahlig).
- Widersprüche zwischen V-1 und Tests wurden nicht gefunden.

## Nicht erreicht

Nichts aus Phase 1. K3 (Web Push) ist manuell und wurde nicht ausgeführt; `/static/` wird ausgeliefert und die VAPID-Variablen werden genutzt. Der Fehlerinjektions-Header ohne `SPIKE_FAULTS=1` (manueller S3-Test) wurde nicht gesondert geprüft; die Logik steht in `op.Base`.

## Auffälligkeiten

- **huma** passt gut zur Aufgabe, brauchte aber Eingriffe: `huma.NewError` umleiten (Fehlerformat), `DefaultArrayNullable=false`, eigener `SchemaNamer` (gleicher Typname in zwei Paketen löst eine Panik beim Start aus), `$ref` für die Schemas je Operation selbst auflösen. Pro Operation entsteht ein eigener Endpunkt; die generischen Anfrage-/Antworthüllen (`request[P]`, `response[R]`) sind die ganze „Magie“. `additionalProperties:false` und `required` ergeben sich aus den Go-Tags (Pflicht = kein `omitempty`).
- **sqlc** mit rekursiven CTEs (Team-Baum) funktioniert; Overrides für `uuid` und `timestamptz` nötig. `jsonb` kam trotz Override als `[]byte`.
- **rrule-go v1.8.2**: kennt keine Zeitzonen-Wanduhr (daher der Eigenbau), lehnt COUNT+UNTIL, INTERVAL=0, BYMONTHDAY=0 und fehlendes FREQ nicht oder nur teilweise ab; alle 21 gültigen und 6 ungültigen Golden-Fälle bestehen mit dem Eigenbau-Klebstoff.
- **go-oidc v3**: ausgereift; Discovery verlangt erreichbaren Issuer (wird beim ersten Zugriff mit Wiederholung bei der nächsten Anfrage nachgeholt). **oauth2** liefert PKCE (`GenerateVerifier`, `S256ChallengeOption`) fertig.
- **webpush-go**: einfach, aber ungetestet gegen einen echten Push-Dienst (K3 manuell). **go-mail**: Kopfzeilen kamen in Mailpit unverändert an.
- **anthropic-sdk-go v1.84.0**: Werkzeugschema muss in `Properties`/`Required`/`ExtraFields` zerlegt werden; `WithMaxRetries(0)` ist wichtig, sonst verbraucht das SDK das Proxy-Budget bei Fehlern.
- **Aufträge**: Die Outbox mit `SKIP LOCKED` kommt mit rund 130 Zeilen aus; eine Bibliothek wie River hätte eigene Tabellen und Migrationen sowie die Zuordnung je Empfänger/Kanal/Versuch nicht abgenommen.
- Docker-Build ohne BuildKit in dieser Umgebung (`--mount` nicht möglich); Modul-Download beim Bauen braucht Netz (Erstbau ca. 90 s).
- K5: beim Abbruch waren 24 von 200 Zustellungen wirksam, danach kamen alle an; 6–8 Duplikat-Versuche wurden vom Mock abgefangen.
- Lastlauf S-8 (`loadcheck.py`, 16 Threads, 30 s, Mischung aus Lesen und Terminanlage, 1 CPU): ca. 59 Anfragen/s, keine Fehler, p95 475 ms; Web ca. 10 MiB, Worker ca. 7 MiB Speicher im Ruhezustand.

## Phase 2 (N-1)

`appointment.reschedule` kostete eine Dateiänderung (`internal/domain/appointment.go`, ca. 40 Zeilen). Annahme: Nur geplante Termine lassen sich verschieben (sonst 409 `conflict`); Prüfung von `ends_at > starts_at` vor dem Laden des Termins (422).
