# Spike E-002 – Kandidat typescript

TypeScript 5.6 (strict) auf Node.js 22; Fastify 5.12.8, Kysely 0.29.9 (+ `pg` 8.23.1), Zod 4.6.7 (ein Schema je Operation → JSON Schema über `z.toJSONSchema`). Ein Image, zwei Startarten (`node dist/main.js web|worker`), mehrstufiger Build (node:22-alpine, nur Produktionsabhängigkeiten, Nutzer `node`).

## Bibliotheken (Auswahl, Version, Reifegrad)

| Zweck | Bibliothek | Version | Erfahrung |
|---|---|---|---|
| RRULE | `rrule` + `luxon` (Zonen) | 2.8.1 / 3.7.2 | Verbreitet, aber seit Jahren kaum gepflegt, CommonJS (unter Node-ESM nur über Default-Import nutzbar, Typen ok). Rechnet nur „schwebend“ (UTC): Wanduhrsemantik muss man selbst herstellen (siehe Eigenbau). Alle 21 gültigen/6 ungültigen Golden-Fälle bestanden; ungültige Eingaben prüft die Bibliothek teils nicht (FREQ=FOO, INTERVAL=0, BYMONTHDAY=0, COUNT+UNTIL) – ergänzt. |
| Token-Prüfung | `jose` | 6.2.18 | Sehr gut gepflegt; `createRemoteJWKSet` + `jwtVerify` ersetzen jeden Eigenbau. |
| OIDC-Code-Flow, PKCE | `openid-client` | 6.9.1 | Gut gepflegt (panva); v6 verlangt `allowInsecureRequests` für http-Keycloak. |
| Web Push | `web-push` | 4.0.0 | VAPID und Verschlüsselung ohne Eigenbau. Ohne Browser nur bis zum Senden geprüft (K3 manuell, nicht Teil der Aufgabe). Reiner ESM-Export mit benannten Exporten. |
| E-Mail | `nodemailer` | 10.6.1 | Unauffällig; ohne TLS/Anmeldung per `ignoreTLS`. |
| KI | `@anthropic-ai/sdk` | 1.12.0 | `baseURL` auf den Schutz-Proxy, `maxRetries: 0`, 60 s Zeitlimit, kein Streaming. Unauffällig. |
| Aufträge | keine Bibliothek: Tabelle `event_recipient` + `FOR UPDATE SKIP LOCKED` + Lease | – | Bewusst einfach gehalten (siehe Annahmen); kein Auftragsframework nötig, weil Web und Worker nur über die Datenbank sprechen. |
| Architekturregel | `dependency-cruiser` | 18.8.0 | Regel in `.dependency-cruiser.cjs`, erfasst auch transitive Abhängigkeiten (`reachable`). |
| Brücke | `json-schema-to-typescript` | 16.0.0 | Typen aus `result_schema`/`params_schema`; Client `bridge/client.ts` einmal von Hand (generisch, nicht je Operation). |
| Logs | `pino` | 10.x | JSON-Zeilen mit `ts`, `level`, `msg`, `correlation_id`, im Worker `event_id`. |
| Test | `vitest` | 5.1.1 | `make test`: Golden-RRULE-Fälle und Ableitungstest. |

## Eigenbau (mit `EIGENBAU:BEGIN/END` markiert)

- `src/domain/rrule.ts`: Umrechnung zwischen Ortszeit und UTC über luxon (Wanduhrsemantik, UNTIL in Ortszeit) und Gültigkeitsprüfungen, die `rrule` nicht leistet (~60 Zeilen). Kein Eigenbau bei Kryptografie, Token-Prüfung, OIDC oder Web Push.

Nicht markiert, weil keine Bibliotheksfunktion ersetzt wird: die Auftragswarteschlange in `src/worker/worker.ts` (SQL-Abholung mit Lease, Wiederholung, Ersatzkanal).

## Eine Beschreibung je Operation (S-1)

`defineOperation({name, description, mutating, params, result, run})` in `src/domain/ops/*.ts`. `src/core/operation.ts` leitet daraus ab: Validierung (Zod), `POST /api/v1/operations/:name`, `GET /api/v1/operations`, `GET /api/v1/ai/tools`, Vorschau und – über `make bridge` – die Typen in `bridge/generated/`. Die Operationsdateien werden beim Start per Verzeichnislesen geladen: Eine neue Operation ist eine neue/geänderte Datei in `src/domain/ops/`, keine Liste ist zu pflegen.
Vorschau = Ausführung in der Transaktion mit anschließendem Rollback (keine zweite Vorschau-Implementierung); die erfassten `affected`-Einträge kommen aus `recordChange`/`ctx.affected`.

## Annahmen

- `preview_supported` ist für alle schreibenden Operationen `true` (die Vorschau funktioniert generisch über Rollback); lesende ignorieren `preview`.
- Ungültiger JSON-Rumpf/ungültige Form des Aufrufs → 422 `validation_error`. `GET /auth/callback` mit unbekanntem `state` → 400 (Fehlerformat mit Code `validation_error`).
- Das Anmelde-`state` wird serverseitig in der Datenbank (`oidc_state`, einmalig verwendbar, 10 min) gehalten, nicht in einem Cookie. Sitzungen: Tabelle `session`, Cookie `chronos_session` (HttpOnly, SameSite=Lax, Path=/; `Secure` nur bei https-Redirect-URL). Operationen akzeptieren Bearer-Token oder Sitzungscookie.
- Verlauf: `actor` ist die `sub` als Zeichenkette. `history.undo` eines Rückgängig-Eintrags setzt zusätzlich `undone=false` am ursprünglichen Eintrag, damit er erneut rückgängig gemacht werden kann. Serien haben ein Statusfeld (`aktiv`/`gelöscht`), damit auch ihre Anlage rückgängig zu machen ist.
- Ereignisse ohne Empfänger (Aufrufer allein im Team) werden trotzdem als Ereignis gespeichert. Die Kanalliste eines Empfängers wird beim Schreiben des Ereignisses festgehalten.
- Zustellung: Wartezeit nach Versuch n = `RETRY_BASE_MS·2^(n-1)`; nach dem 3. Fehlversuch sofort der nächste Kanal. Lease 15 s; nach `SIGKILL` werden unfertige Zustellungen nach Ablauf der Lease erneut versucht (gleicher Idempotenzschlüssel). Fehlende E-Mail-Adresse → `skipped`.
- `notification.list`: älteste zuerst mit `limit` (Standard 100); `cost.list`: neueste zuerst (Standard 100, Höchstwert 500 – im Vertrag nicht festgelegt).
- Kostenposten KI: `ceil((in·Preis_in + out·Preis_out) / 1 000 000)` Mikro-Euro, Verursacher = Aufrufer.
- `make bridge`/`make arch-check`/`make test` brauchen lokal `npm ci` (läuft automatisch). `bridge/generated/` ist erzeugt, aber eingecheckt.
- Widersprüche zwischen V-1 und den Tests wurden nicht gefunden.

## Ergebnis Selbsttest (Phase 1)

Abnahmesuite: S1 7/7, S2 6/6, S3 6/6 (1 manuell übersprungen), K2 29/29, K4 4/4, K5 1/1 (beim Abbruch 32 wirksam, 7 Duplikat-Versuche), K6 1/1, M14 6/6, M15 1/1, S10 3/3. Lastlauf zur Selbstkontrolle (S-8): 6000 Aufrufe, 40 parallel, 0 Fehler, p50 66 ms, p99 198 ms; Web ≈ 67 MiB. K3 nicht ausgeführt (manuell, nicht Teil der Aufgabe).

## Auffälligkeiten

- ESM-Interop: `rrule` (CJS) und `web-push` (ESM mit benannten Exporten) liefen unter `tsx`/`vitest` und scheiterten erst im Container (`node dist/main.js`) – einzige Korrekturschleife außer dem Erstlauf. Test im gebauten Image statt nur unter `tsx` lohnt sich.
- Zod 4 erzeugt JSON Schema mit `$schema`; es wird entfernt, damit `input_schema` und `params_schema` identisch und für die Anthropic-API unauffällig sind.
- Nicht erreichte Aufgaben: keine in Phase 1 (K3 manuell).
