# Spike E-002, Kandidat rust

Rust 1.100 (stabil), axum 0.8.9, sqlx 0.9.1, serde 1.0.229 / serde_json 1.0.154, utoipa 6.0.0. Ein Image (`chronos-spike-rust`, ~160 MB, Debian-slim, Nicht-Root UID 10001), Startmodus `web` oder `worker`; mehrstufiger Build mit Abhängigkeits-Cache (Platzhalter-`main.rs`), Release-Profil (thin LTO, strip). Abnahmesuite Phase 1: 64 bestanden, 1 manuell übersprungen (S3-Header ohne `SPIKE_FAULTS`); K3 (Web Push) nicht ausgeführt (manuell).

## Aufbau
- `src/core/ops.rs`: **einzige Beschreibung je Operation**: Trait `Operation` (Name, Beschreibung, mutating, Vorschau, `Params`/`Result` mit `serde` + `utoipa::ToSchema`) plus `register!(Typ)` (Sammlung per `inventory`). Daraus entstehen JSON-Schemas (utoipa, Referenzen aufgelöst, `additionalProperties:false`), Validierung (`jsonschema`), Endpunkt, `/api/v1/operations`, `/api/v1/ai/tools` und die Brückentypen. Eine neue Operation = eine Datei/Stelle mit `impl Operation` + `register!`.
- `src/domain/` (Teams, Termine, Serien, Verlauf) kennt `src/channels/` nicht. `make arch-check` (`tools/arch-check.sh`) prüft: kein Verweis auf channels/Kanalbibliotheken und Positivliste (`crate::core|error|register|domain`). Ein eingebauter Verstoß wird in ~10 ms gemeldet (Exit 1, Datei:Zeile).
- `src/core/changes.rs`: Zustand + Verlauf + Ereignis (+ Zustellaufträge je Empfänger) in **einer** sqlx-Transaktion; Fehlerinjektion `after_history` dazwischen.
- `src/worker/`: Auftragstabelle `delivery_tasks` (`FOR UPDATE SKIP LOCKED`, Lease 30 s), je Versuch eine Zeile in `deliveries`, 3 Versuche je Kanal (`RETRY_BASE_MS`, ×2), dann Ersatzkanal; `skipped` ohne Voraussetzung; E-Mail-Kosten in derselben Transaktion wie die Erfolgszeile. Web und Worker sprechen nur über die Datenbank.
- `src/auth/`: Bearer-Prüfung (JWKS, `iss`, `exp`), OIDC-Code-Flow mit PKCE S256 + `state` + `nonce`, Sitzungen und Flow-Zustand in der Datenbank (Abmeldung = Zeile löschen).
- `bridge/` + `tools/bridge-gen.mjs`: `make bridge` holt `/api/v1/operations` und erzeugt `bridge/generated/operations.ts` (`OperationMap`, Typen per json-schema-to-typescript); `bridge/client.ts` (generisch, von Hand, ~30 Zeilen) macht `call(name, params)` abhängig vom Namen typisiert.

## Bibliotheken (Version laut Cargo.lock)
| Zweck | Bibliothek | Reifegrad / Hinweise |
|---|---|---|
| HTTP / DB / Serialisierung / Schema | axum 0.8.9, sqlx 0.9.1, serde, utoipa 6.0.0 (vorgegeben) | sqlx 0.9 verlangt `AssertSqlSafe` für dynamische SQL-Strings (Übersetzungsfehler, einmal). utoipa erzeugt OpenAPI-3.1-Schemas mit `$ref` und `["x","null"]`-Typen; für Draft 2020-12 / KI-Werkzeuge musste nachbearbeitet werden (Referenzen inline, Null-Varianten in Parametern entfernt, `additionalProperties:false`) – siehe `normalize` in `core/ops.rs`. |
| Validierung | jsonschema 0.61.2 | validiert Parameter gegen dasselbe `params_schema`. |
| Registrierung | inventory 0.3.25 | verteilte Registrierung ohne zweite Liste. Interior-mutable Statics (OnceLock im Eintrag) sind nicht erlaubt → Cache separat. |
| RRULE | rrule 0.14.0 + chrono-tz 0.10.4 | Wanduhrsemantik/Sommerzeit, BYSETPOS, WKST, EXDATE: alle 21 Golden-Fälle bestanden. **Problem:** akzeptiert stillschweigend `COUNT`+`UNTIL`, `INTERVAL=0`, `BYMONTHDAY=0` → Vorprüfung nötig (Eigenbau, s. u.). |
| Anmeldung (OIDC) | openidconnect 4.1.0 (Discovery, PKCE, Code-Tausch, ID-Token-Prüfung) | ausgereift; Typzustand-Client (`CoreClient<EndpointSet,…>`) macht Rückgabetypen sperrig. Bringt eigene reqwest-0.12-Instanz mit (`openidconnect::reqwest`). |
| Bearer-JWT | jsonwebtoken 12.0.0 (`rust_crypto`) | **Version 12 braucht ein explizit gewähltes Crypto-Backend**, sonst Panik zur Laufzeit (`CryptoProvider`); JWKS-Abruf und Cache sind eigener Leim (`auth/mod.rs`), die Prüfung selbst nicht. |
| Aufträge | keine Bibliothek: Tabelle + `SKIP LOCKED` (sqlx) | Für diesen Umfang einfacher als apalis/Ähnliches; Wiederanlauf über Lease und Freigabe beim Start. |
| E-Mail | lettre 0.11.24 (SMTP ohne TLS, tokio) | ausgereift; eigene Kopfzeilen brauchen je einen `Header`-Typ (Makro `text_header!`). |
| Web Push | web-push 0.11.0 (`hyper-client`) | funktioniert nach Dokumentation (VAPID Base64-Schlüssel, aes128gcm); **zieht OpenSSL** (ece, hyper-tls) → Laufzeitabbild Debian mit `libssl3` statt `static`/musl. Ohne Browser nicht ausgeführt (K3 manuell). |
| KI | **kein** SDK: reqwest 0.13.5 direkt auf `POST /v1/messages` | Es gibt kein offizielles Rust-SDK; Community-Crates wirkten weniger gepflegt. Der Aufruf ist klein, daher Eigenbau (s. u.). |
| Sonstiges | tokio 1.54.1, tower-http 0.7.1 (`/static/`), tracing 0.1.44 + tracing-subscriber 0.3.23, uuid 1.29.3, chrono 0.4.45, futures 0.3.34 | |
| Brücke (Node) | json-schema-to-typescript 15.0.4 (npm), TypeScript 5.6 (Prüfer) | `make bridge` braucht Node/npm und Netz. |

## Eigenbau (mit `EIGENBAU:BEGIN/END` im Quelltext)
1. `src/logging.rs`: JSON-Logformat mit den Feldern `ts`, `level`, `msg`, `correlation_id` (tracing-subscriber liefert `timestamp`/`message`/verschachtelte Felder); Korrelations-ID über eine Task-Local.
2. `src/domain/series.rs` (`precheck`): RFC-5545-Prüfungen, die `rrule` nicht macht (COUNT+UNTIL, INTERVAL/COUNT ≥ 1, BYMONTHDAY/BYYEARDAY/BYWEEKNO/BYSETPOS ≠ 0 und im Bereich). Die RRULE-Ausdehnung selbst kommt aus der Bibliothek.
3. `src/ai/mod.rs`: Anthropic-Messages-Aufruf (Anfrage bauen, Antwort lesen, `tool_use` auf Operationsnamen abbilden).
Nicht eigengebaut: Kryptografie, Token-Prüfung, OIDC-Fluss, SMTP, Web-Push-Verschlüsselung.

## Annahmen
- Parameterfehler (Schema, Typen, `ends_at ≤ starts_at`, unbekannte Zeitzone, ungültige Ortszeit) → 422 `validation_error`; ungültiger Anfragekörper ebenfalls. Vorschau bei Operationen ohne Vorschau → 422.
- Reihenfolge der Prüfungen: Authentifizierung (401) vor Operationssuche (404).
- `appointment.create` mit `preview:true` liefert `id` = Nil-UUID (Objekt existiert noch nicht).
- Team-Operationen erzeugen keinen Verlaufseintrag (V-1 nennt ihn nur für Termine/Serien). Der Verlauf trägt `team_id` (nicht in der API sichtbar), damit `history.list` nach effektiver Mitgliedschaft filtern kann.
- Rückgängig eines Rückgängig setzt `undone` des ursprünglichen Eintrags wieder auf `false`. Ereignis `change.reverted` übernimmt die Empfänger des Ereignisses des rückgängig gemachten Eintrags (ohne Ereignis: leere Empfängerliste, Ereignis wird trotzdem festgehalten).
- Serien haben einen Status `aktiv`/`gelöscht` (für Rückgängig von `series.create`); gelöschte Serien sind 404.
- Kanäle der Person werden zum **Zustellzeitpunkt** gelesen (nicht beim Ereignis). Fehlende E-Mail-Adresse → `skipped`.
- Ein Worker-Prozess: Beim Start gibt er alle Sperren frei; zusätzlich Lease 30 s. Parallelität 4 (`WORKER_CONCURRENCY`), sonst wäre K5 wegen schneller Abarbeitung nicht aussagekräftig.
- `notification.list`/`cost.list`: `limit` Standard 100 (max 500); `cost.list` neueste zuerst.
- Sitzungen laufen nicht ab (Spike). Das Cookie hat kein `Secure` (HTTP-Testumgebung).
- `/api/v1/operations/{name}` akzeptiert neben Bearer auch das Sitzungs-Cookie.

## Nicht erreicht / nicht geprüft
- K3 (Web Push) manuell, nicht ausgeführt; der Code nutzt die VAPID-Variablen und `/static/` wird ausgeliefert.
- S3-Hinweisfall „Header ohne `SPIKE_FAULTS` wirkungslos“ nicht automatisch geprüft (Code: Header wird nur bei `SPIKE_FAULTS=1` ausgewertet).

## Auffälligkeiten
- **Node-`fetch` sperrt Port 10080** („bad port“, undici-Liste gesperrter Ports); der Brückengenerator nutzt daher `node:http`. Betrifft jeden Node-Client gegen diese Umgebung.
- Widersprüche zwischen V-1 und Tests: keine gefunden.
- Lastlauf zur Selbstkontrolle (S-8, 16 Threads Python, 20 s, `appointment.create` mit einem Empfänger, Container mit 1 CPU): 52 Anfragen/s, 0 Fehler, p50 306 ms, p99 590 ms (Client und Keycloak-JWT-Prüfung eingeschlossen); Web 6 MiB, Worker 4 MiB Speicher im Leerlauf danach.
- K5: beim Abbruch 16 von 200 wirksam, nach Neustart alle, 4 Duplikat-Versuche (vom Mock abgefangen).
- Korrekturschleifen: siehe `PROTOKOLL.md`.
- Aufruf der Unit-Tests: `make test` (6 Tests: Operationsbeschreibung konsistent, KI-Werkzeuge = Operationen, Validierung, RRULE-Wanduhr/Vorprüfung/Limit).
