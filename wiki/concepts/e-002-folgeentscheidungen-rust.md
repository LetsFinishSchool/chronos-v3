---
title: Offene Folgeentscheidungen von E-002 unter der Annahme Rust
type: concept
sources:
  - docs/arc42/09-entscheidungen/ADR-004-sprache-und-laufzeit.md (Entwurf, Abschnitt „Was an dieser Entscheidung hängt“)
  - docs/arc42/09-entscheidungen/01-offene-entscheidungen.md
  - docs/arc42/09-entscheidungen/ADR-003-datenbank-postgresql.md
  - docs/arc42/08-konzepte/K-002-berechtigung-und-zugang.md
  - docs/arc42/08-konzepte/K-006-operationsschicht-und-assistent.md
  - docs/arc42/08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md
  - docs/vision/product-vision.md (PWA)
  - spikes/e-002/ergebnisse/rust/rust/README.md, src/core/ops.rs, src/ai/mod.rs, src/auth/mod.rs, tools/arch-check.sh (Spike-Stand 2026-11-23)
  - spikes/e-002/reports/q4-pflegestand.md
  - https://platform.claude.com/docs/en/cli-sdks-libraries/overview (abgerufen 2026-11-23)
confidence: mittel
last-verified: 2026-11-23
---

# Offene Folgeentscheidungen von E-002 unter der Annahme Rust

**Status:** Arbeitsgrundlage für den Product Owner, **keine Entscheidung**. ADR-004 (Rust) ist seit 2026-11-23 freigegeben; E-005 ist entschieden (ADR-005), die übrigen Punkte sind offen. Die Punkte „Offen vor der Freigabe“ von ADR-004 selbst (RRULE, Web Push, Sicherheitsmeldungen, Wiederholungslauf, VAPID-Lücke) stehen dort mit Optionen und werden hier nicht wiederholt.

Übersicht:

| # | Entscheidung | Was Rust ändert | Vorschlag (unverbindlich) |
|---|---|---|---|
| 1 | E-005 Form der Operationsschicht | Spike-Form (Trait + `inventory` + utoipa) ist belegt; Typsystem kann Vorschau- und Rechtepflicht erzwingen | A, Schema-Quelle prüfen (D) |
| 2 | E-004 Frontend-Ansatz | Frontend bleibt praktisch TypeScript; Rust-WASM ist die einzige Ein-Sprachen-Variante | A (SPA + PWA, statisch aus axum) |
| 3 | E-008 Keycloak, Sitzung, Gast | Serverseitiger Code-Flow im Spike gebaut; Rollen per Typzustand trennbar | A (BFF-Sitzung im Cookie) |
| 4 | E-009 KI-Anbindung | Kein offizielles SDK, Eigenbau ist Dauerpflege | A (eigener schmaler Client hinter Anbieterschnittstelle) |
| 5 | E-016 Teststrategie, Architekturtests | Crate-Grenzen erzwingen Abhängigkeitsregeln im Compiler; `sqlx::test` für DB-Tests | C (Workspace + `cargo-deny`) |
| 6 | Migrationswerkzeug (ADR-003) | `sqlx migrate` ist schon im Baum | A, als Job vor dem Rollout |
| 7 | K-007 Übersetzungsformat, Plural/Datum | Fluent ist das Rust-native Format; ICU4X für Formate | A (Fluent) oder B (JSON/ICU), hängt an E-004 |
| 8 | **neu:** Zeitbibliothek | `chrono`/`chrono-tz` „unmaintained“, `jiff` ist Plan B für RRULE | eigene Entscheidung, mit ADR-004 Punkt 1 |
| 9 | **neu:** Build, CI, Lieferkette | Bauzeit, Plattenbedarf, 375 Crates | Build-Cache + `cargo-deny` als Pflicht |

Empfohlene Reihenfolge: E-005 → E-008 und E-004 gemeinsam (Sitzungsmodell bestimmt das Frontend) → E-016, Migration, Build (klein, früh nötig) → K-007 (nach E-004) → E-009 (nach E-005). Zeitbibliothek zusammen mit ADR-004 Punkt 1.

---

## 1. E-005 Form der Operationsschicht

**Entschieden (PO 2026-11-23): V2**, siehe [ADR-005](../../docs/arc42/09-entscheidungen/ADR-005-operationsschicht.md). Die Optionen unten sind überholt und nur noch Herleitung.

**Ausführlich:** [E-005-Analyse](../../docs/arc42/09-entscheidungen/E-005-operationsschicht-analyse.md) (Entwurf, Teilfragen T1 bis T6, Varianten V1 bis V3). Befund dort: Der Spike prüft die Berechtigung in jeder Operation (19 Stellen), schreibt den Verlauf von Hand und hat eine Vorschau nur bei 4 von 10 schreibenden Operationen.

**Rust-Folge:** Der Spike hat die Form „eine Definition erzeugt alles“ belegt: `impl Operation` (Name, Beschreibung, `MUTATING`, `Params`/`Result` mit `serde` + `utoipa::ToSchema`) plus `register!` über `inventory`; daraus Endpunkt, Validierung (`jsonschema`), `/api/v1/ai/tools` und Brückentypen. Neue Operation = 1 Datei (M-11). Eigenbau: `normalize` in `core/ops.rs`, weil utoipa OpenAPI-3.1-Schemas liefert, KI-Werkzeuge aber JSON Schema ohne `$ref` brauchen. Vergleich: entspricht einem Spring-Bean mit Annotation, das per Classpath-Scan eingesammelt wird; `inventory` ersetzt den Scan zur Link-Zeit.

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** Trait + verteilte Registrierung (wie Spike), verschärft: eigener Trait `MutatingOperation` mit Pflichtmethode `preview`, `Ctx` nur über Rechteprüfung erzeugbar | Belegt im Spike; Compiler erzwingt K-006 (keine schreibende Operation ohne Vorschau) und K-002 (Prüfung an einer Stelle); 1 Datei je Operation | utoipa: 1 Owner, viele offene Issues; `normalize` bleibt Eigenbau; `inventory` beruht auf Link-Zeit-Magie (fehlt eine Registrierung, merkt es nur ein Test) |
| **B** Eigenes Attribut-Makro (`#[operation(name = "...", mutating)] async fn …`) | Am wenigsten Boilerplate; deklarativ, für Agenten gut lesbar | Eigenes Proc-Macro-Crate = Eigenbau; Makrofehler schwer zu lesen; längere Bauzeit |
| **C** Schema-first: Operationen in YAML/JSON Schema, Rust- und TS-Typen generiert | Sprachneutral; übersteht einen späteren Sprachwechsel (ADR-001 Rang 1) | Zwei Artefakte (Beschreibung + Implementierung) können auseinanderlaufen; Rust-Codegeneratoren aus JSON Schema weniger ausgereift; `build.rs`-Komplexität |
| **D** Wie A, aber `schemars` statt utoipa als Schemaquelle | `schemars` erzeugt JSON Schema (Draft 2020-12) direkt, das passt zum KI-Werkzeugformat; `normalize` schrumpft | OpenAPI-Dokument und Swagger-UI entfallen oder brauchen ein weiteres Crate; vor Wahl kurz prüfen (Spike-Erweiterung, < 1 h Agentenzeit) |

## 2. E-004 Frontend-Ansatz

**Rust-Folge:** Der Q-5-Vorteil von Rust (Vorschau und Schreibmerkmal in den Typen) wirkt nur, wenn das Frontend die generierten TypeScript-Typen nutzt. Web Push braucht in jeder Variante einen Service Worker in JavaScript. Die Produktvision nennt PWA. Kein Node-Prozess zur Laufzeit, sonst gehen ADR-002 (zwei Prozesse) und der Ressourcenvorteil verloren (TypeScript-Spike: ~90 MiB).

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** SPA in TypeScript (Vue oder Svelte) als PWA, statisch gebaut und von axum (`tower-http` `ServeDir`) ausgeliefert | Brücke aus dem Spike direkt nutzbar; Service Worker, Installierbarkeit und Push ohne Sonderweg; großes Ökosystem, Agenten kennen es gut | Zwei Werkzeugketten (cargo + npm) und zwei Lieferketten; Bundle-Größe auf dem Smartphone im Blick halten (QA-008 < 1 s); Barrierefreiheit: SPA muss Fokus bei Seitenwechsel selbst setzen und den Wechsel ansagen (WCAG 2.4.3 Fokusreihenfolge, `aria-live`-Region), das liefert der Browser nur bei echter Navigation |
| **B** Serverseitig gerendert in Rust (askama oder maud) + htmx, wenig JS (Service Worker) | Eine Sprache für fast alles; Vorlagen werden übersetzt und geprüft; kleinster Client, schnelle erste Seite; semantisches HTML und Browser-Navigation bringen Barrierefreiheit „umsonst“ | Q-5-Vorteil ungenutzt; jede UI-Änderung kostet einen Rust-Build (langsame Rückkopplung); interaktive Teile (Terminfindung FA-006) mühsam; i18n im Server und im Service Worker getrennt |
| **C** Rust/WASM (Leptos, Dioxus) mit SSR und Hydration | Eine Sprache, Typen ohne Generator geteilt | WASM-Bundle groß für „mobil zuerst“; Frameworks vor 1.0 mit Brüchen; wenige barrierefreie Komponentenbibliotheken; Service Worker trotzdem JS; Agenten schwächer |
| **D** Meta-Framework mit Node-Server (Nuxt, SvelteKit SSR) als BFF | Bestes SSR- und SPA-Erlebnis | Dritter Prozess mit Node-Grundspeicher; hebt den Rust-Vorteil auf; widerspricht ADR-002 → praktisch ausgeschlossen |

Folgefrage zu A: Vue (bekannt beim Product Owner) oder Svelte (kleinere Bundles). Angular ist für „mobil zuerst“ eher schwer. SvelteKit/Nuxt im statischen Modus (ohne Node zur Laufzeit) fallen unter A.

## 3. E-008 Keycloak, Sitzung, Gast-Identität

**Rust-Folge:** K-002 verlangt „Zugangstoken für Skripte der Seite nicht lesbar“, das spricht für Tokens nur im Server. Der Spike hat genau das gebaut (`openidconnect`, PKCE S256, `state`, `nonce`, Sitzung in PostgreSQL, Abmeldung = Zeile löschen). Stolperstellen: `openidconnect` hat einen Owner; `jsonwebtoken` 12 braucht ein ausdrücklich gewähltes Krypto-Backend, sonst Panic zur Laufzeit. Rust-spezifisch: Typzustand `Ctx<Member>` / `Ctx<Guest>`, sodass Gast-Operationen schon beim Übersetzen auf das Erlaubte beschränkt sind (vergleichbar mit getrennten Security-Kontexten in Spring, aber im Typ statt zur Laufzeit).

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** BFF: Code-Flow im Server, Sitzung in PostgreSQL, Cookie `HttpOnly; Secure; SameSite=Lax` | Erfüllt K-002; im Spike belegt; Gast nutzt denselben Cookie-Mechanismus | CSRF-Schutz nötig (SameSite + Origin-Prüfung); Refresh-Token-Behandlung und Ablauf sind Eigenbau (Spike: Sitzungen ohne Ablauf); Sitzungszugriff je Anfrage auf die DB |
| **B** Token im Browser (SPA als öffentlicher Client, Bearer an die API) | Server zustandslos, nur `jsonwebtoken`-Prüfung | Verstößt gegen K-002 (XSS liest Token); nur der Vollständigkeit halber |
| **C** Vorgeschalteter Proxy (z. B. oauth2-proxy) | OIDC-Code verlässt Chronos, weniger eigene Lieferkette | Weiterer Container im Budget; Gast-Zugang passt nicht ins Proxy-Modell; weniger Kontrolle |

Gast-Identität (sprachneutral, aber zu entscheiden): (i) Link-Token beim ersten Aufruf gegen ein Gast-Cookie tauschen und aus der Adresse entfernen (kein Leck über Verlauf/Referer); (ii) weiteres Gerät = Link erneut öffnen; (iii) optional Wiedererkennung per E-Mail-Link (`lettre` ist schon im Baum). Die Ablage der Link-Token (QA-007, gehasht wie Passwörter) gehört dazu.

## 4. E-009 KI-Anbindung

**Rust-Folge:** Laut Claude-Dokumentation (abgerufen 2026-11-23) gibt es offizielle SDKs für Python, TypeScript, C#, Go, Java, PHP, Ruby, **nicht für Rust**. Der Spike nutzt `reqwest` direkt und sendet `anthropic-version: 2023-06-01`; die Dokumentation nennt bereits eine API-Version `2026-10-21`. Das zeigt die Dauerpflege des Eigenbaus. Die Anbieterschnittstelle (anbieterneutral, K-006) und die Kostenerfassung je Aufruf (RB-010) sind in jeder Option nötig.

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** Eigener schmaler Client je Anbieter hinter Trait `AiProvider` | Wenige Abhängigkeiten; volle Kontrolle über `usage` für die Kostenerfassung und über das Limit; Werkzeugschemas kommen aus E-005 | API-Versionen, Fehlercodes, Wiederholung mit Backoff, ggf. Streaming (SSE) selbst pflegen |
| **B** Community-Crate (Anthropic-spezifisch oder Mehr-Anbieter-Bibliothek) | Weniger Eigencode; Mehr-Anbieter-Crates bringen Neutralität mit | Pflegestand unklar (Q-4 schon schwach); Abstraktion kann `usage` und Fehlversuche verdecken (RB-010); Lieferkette wächst |
| **C** OpenAI-kompatible Schnittstelle als gemeinsamer Nenner | Ein Client für viele Anbieter | Anthropic beschreibt die Kompatibilitätsschicht als Testhilfe mit Kernfunktionen, nicht als vollen Funktionsumfang; Werkzeugnutzung und Kosten-Details können fehlen |
| **D** Sidecar mit offiziellem SDK (TS/Go) | Offizielles SDK | Dritter Prozess, widerspricht ADR-002 und Budget → praktisch ausgeschlossen |

## 5. E-016 Teststrategie und Architekturtests

**Rust-Folge:** Der Spike prüft die Regel „domain kennt channels nicht“ per `grep` (`tools/arch-check.sh`, 10 ms). In Rust kann der Compiler das übernehmen, wenn Bausteine eigene Crates sind (vergleichbar mit Maven-Modulen bzw. JPMS statt ArchUnit). Weitere Rust-Hilfen: `#[sqlx::test]` legt je Test eine frische Datenbank an; `sqlx::query!` prüft SQL beim Übersetzen (in CI mit `cargo sqlx prepare`/`.sqlx`-Dateien); `tower::ServiceExt::oneshot` testet axum-Router ohne Netz.

| Option (Architekturregeln) | Vorteile | Nachteile |
|---|---|---|
| **A** Cargo-Workspace, ein Crate je Baustein (core, domain, channels, web, worker) | Regel vom Compiler erzwungen, kein Zusatzwerkzeug; Zyklen unmöglich; paralleles, inkrementelles Bauen | Mehr `Cargo.toml`; Orphan-Regel (fremder Trait für fremden Typ) erzwingt manchmal Hilfstypen; Umzüge zwischen Crates aufwendiger |
| **B** Ein Crate, Sichtbarkeit (`pub(crate)`) + Skript wie im Spike | Einfach, im Spike belegt | `grep` übersieht Makros, Re-Exporte, voll qualifizierte Pfade; Regel nur so gut wie das Skript |
| **C** A für harte Grenzen + `cargo-deny` (`bans`) für verbotene Bibliotheken je Crate | Doppelte Absicherung, auch Lieferkette in derselben Prüfung | Zwei Mechanismen zu pflegen |

Testebenen (Vorschlag unabhängig von der Option): Unit-Tests im Modul; DB-Tests mit `#[sqlx::test]` gegen echtes PostgreSQL (statt Testcontainers je Test); Szenariotests aus Kapitel 6 über HTTP; Differenztest RRULE gegen python-dateutil und Property-Tests (`proptest`) für Serien; Snapshot-Tests (`insta`) für Operations- und Werkzeugschemas, damit Schemaänderungen im Review sichtbar werden; Läufer `cargo-nextest`.

## 6. Migrationswerkzeug (ADR-003)

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** `sqlx migrate` (eingebettet per `sqlx::migrate!`) | Schon im Baum; Prüfsummen; sperrt per Advisory-Lock, Web und Worker starten nicht doppelt; dieselben Migrationen für `#[sqlx::test]` | Keine Rückwärts-Migrationen ohne eigene `down`-Dateien; nur SQL |
| **B** `refinery` | Auch Migrationen in Rust-Code | Zusätzliche Abhängigkeit ohne klaren Mehrwert gegenüber A |
| **C** Sprachneutrales Werkzeug (Flyway, Atlas, dbmate) als eigener Job | Übersteht einen Sprachwechsel; Atlas kann Schemadiffs | Zweites Werkzeug und Image; `sqlx::query!` braucht trotzdem das Schema |

Teilfrage: Ausführung beim Start (einfach, Lock vorhanden) oder als Kubernetes-Job/Init-Container vor dem Rollout (Fehler blockiert den Rollout statt den Pod). Das Importwerkzeug (E-017) nutzt dieselben Migrationen.

## 7. K-007 Übersetzungsformat, Plural- und Datumsformate

**Rust-Folge:** Benachrichtigungen werden im Worker je Empfänger übersetzt (K-007), also braucht der **Server** Übersetzungen, nicht nur das Frontend. Das Format sollte in beiden Welten lesbar sein. Für Datums-, Zahl- und Pluralregeln ist ICU4X (Unicode-Projekt, Rust-nativ, CLDR-Daten, nur de/en einbaubar) der naheliegende Baustein; im Browser genügt die `Intl`-API ohne Bibliothek.

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** Fluent (`.ftl`), Server `fluent-rs`, Browser `@fluent/bundle` | Ein Format für Server und Client; Plural und Geschlecht in der Nachricht selbst; für Übersetzende lesbar | Kleineres Ökosystem als i18next; Werkzeuge (Extraktion, Übersetzungsplattform) weniger verbreitet |
| **B** JSON mit ICU MessageFormat, Browser vue-i18n/FormatJS | Frontend-Standard; Plattformen wie Weblate können es | Rust-Unterstützung für MessageFormat dünner; Gefahr eines zweiten Formats im Server |
| **C** gettext PO | Ausgereifte Übersetzungswerkzeuge (Poedit, Weblate) | Rust-Crates teils C-Bindungen; im Frontend unüblich; Pluralformeln als C-Ausdruck |
| **D** `rust-i18n` (YAML/JSON, Makro `t!`) im Server, eigenes Format im Frontend | Schnell eingerichtet, Schlüssel beim Übersetzen geprüft | Zwei Formate; Pluralregeln einfach |

Bei E-004 B (Server-Rendering) entfällt die Client-Seite, dann spricht mehr für A.

## 8. Neu: Zeitbibliothek (nicht in Kapitel 9)

**Rust-Folge:** `chrono` und `chrono-tz` sind laut RUSTSEC „unmaintained“, `chrono-tz` ist archiviert (q4-pflegestand.md). `rrule` 0.14 hängt an `chrono`; Plan B (E-002a) nutzt `jiff`.

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** `chrono` + `chrono-tz` (wie Spike) | Passt zu `rrule`, `sqlx`, `utoipa` ohne Leim | Ausnahme im Audit dauerhaft; Zeitzonendaten aus archiviertem Repo (K-007 fordert Aktualisierung) |
| **B** `jiff` überall, Zeitzonen aus der Systemdatenbank oder eingebettet | Gepflegt, DST-Semantik eindeutig; passt zum RRULE-Plan B | Leim zu `sqlx`/`utoipa`/`rrule` prüfen; RRULE-Wechsel wahrscheinlich nötig (Eigenbau 12,5 %) |
| **C** `jiff` im Fachkern, `chrono` nur an den Rändern (`rrule`) | Schrittweiser Wechsel | Zwei Zeittypen mit Umrechnung an der Grenze |

## 9. Neu: Build, CI und Lieferkette (nicht in Kapitel 9)

**Rust-Folge:** `target` 4 bis 5 GB je Klon, lange Bauzeit (ADR-004 Folgen), 375 Crates, Sicherheitsmeldungen als begründete Ausnahmen. Image: Debian-slim wegen OpenSSL aus `web-push`; ohne OpenSSL (E-002b) wäre `distroless/cc` oder statisch mit musl möglich.

| Option | Vorteile | Nachteile |
|---|---|---|
| **A** `cargo-deny` in CI als harte Prüfung (Advisories, Lizenzen, Quellen, Bans) mit dokumentierten Ausnahmen in `deny.toml` | Ausnahmen sind im Repo nachvollziehbar (ADR-004 Punkt 3); deckt E-016 C mit ab | Neue Meldungen blockieren Merges, kurzfristige Pflege |
| **B** Nur `cargo audit` als Warnung | Kein Blockieren | Meldungen werden übersehen (RA-003, eine Person) |
| **C** A + `cargo-vet` (geprüfte Crates) | Stärkste Lieferkettenkontrolle | Für eine Person mit 375 Crates kaum leistbar |

Dazu ohne echte Alternative: `rust-toolchain.toml` (feste Toolchain), Build-Cache in GitHub Actions (Cache für `target` und Registry), `cargo-chef` im Dockerfile (Spike nutzt Platzhalter-`main.rs`), Renovate oder Dependabot für Updates.
