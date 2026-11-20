---
title: E-002 Sprach- und Laufzeitwahl, Analyse
status: entwurf
quellen: [ADR-001, ADR-002, ADR-003, req42 RB-003, QA-001, QA-003, FA-014, FA-008, FA-015]
---

# E-002: Sprach- und Laufzeitwahl, Analyse

Entscheidungsvorlage für E-002. **Hinweis zur Belastbarkeit:** Speicherwerte, Bibliotheken und Einschätzungen stammen aus dem Wissen des Assistenten (Stand Mitte 2026), **nicht** aus einer Prüfung der aktuellen Versionen oder des Pflegestands. Vor einer Entscheidung sind die mit ▲ markierten Bibliotheken zu verifizieren, am besten durch einen zeitlich begrenzten Spike (siehe unten).

## Vorentscheidung des Product Owners

Am 2026-11-20 ausgeschieden (Entwurf, wie die übrigen Entscheidungen noch ohne Freigabe):

- **Java/Kotlin:** wegen der hohen RAM-Last.
- **Python:** Die Vorteile gegenüber TypeScript wiegen den zusätzlichen Speicherverbrauch nicht auf.

Verbleibende Kandidaten: **TypeScript, Go, Rust**. Je Kandidat folgt ein Spike nach den Kriterien in [E-002-spike-kriterien](E-002-spike-kriterien.md). Die Abschnitte zu Java/Kotlin und Python bleiben zur Nachvollziehbarkeit stehen.

## Anforderungen an die Sprache (aus den Entscheidungen)

1. **Änderbarkeit (Platz 1):** Modulgrenzen prüfbar oder erzwingbar; neue Operation erscheint automatisch beim Assistenten (eine Beschreibung → API, UI-Formular, KI-Werkzeug).
2. **Bedienbarkeit mobil (Platz 2):** Das Frontend soll mobil-zuerst und einfach sein; Aufwand für die Brücke zwischen Backend und Frontend zählt mit.
3. **Ressourcen (Platz 3):** Zwei Prozesse plus PostgreSQL im Budget von ~1 GiB.
4. **Fachlich:** volle RRULE (RFC 5545) mit Zeitzonen, iCalendar-Ausgabe, Web Push, SMTP, OIDC (Keycloak), KI-SDK, Auftragsabarbeitung mit Wiederholung, Mehrsprachigkeit, S3, Verschlüsselung für Backup.
5. **Betrieb:** Ein Mensch plus Agenten. Wenig Eigenbau, schnelle Rückkopplung (Build/Test), gute Fehlermeldungen für Agenten.

## Bewertungsübersicht

`++` sehr gut, `+` gut, `o` mittel, `-` schwach. Gewichtung nach [ADR-001](ADR-001-prioritaet-der-qualitaetsziele.md); die Einträge sind Einschätzungen, keine Messungen.

| Kriterium | TypeScript | Go | Kotlin/Java | Python | Rust |
|---|---|---|---|---|---|
| Modulgrenzen prüfbar/erzwingbar (1) | + (Linter, Projekte) | + (`internal`, Linter) | ++ (ArchUnit, Module) | o (import-linter) | ++ (Crates, Compiler) |
| Eine Operationsbeschreibung für API, UI, Assistent (1, 2) | ++ (Schema → Typen → JSON-Schema) | o | + | + (pydantic → OpenAPI) | o (utoipa, serde) |
| Gemeinsame Sprache mit Frontend (2) | ++ | - | - | - | - |
| Grundlast je Prozess (3) | o (60–120 MB) | ++ (15–40 MB) | o bis - (60–120 MB nativ; 250 MB+ JVM) | + (50–90 MB) | ++ (5–20 MB) |
| RRULE, Zeitzonen, iCalendar (fachlich) | o ▲ | o ▲ | + | ++ | o ▲ |
| Web Push, SMTP, OIDC (fachlich) | + | + | + | + | o |
| KI-SDK (fachlich) | ++ (offiziell) | + (offiziell) | + (offiziell) | ++ (offiziell) | - (nur Community ▲) |
| Postgres-Auftragsabarbeitung (E-006) | + | ++ | + | + | o |
| Build-/Testgeschwindigkeit (5) | + | ++ | o | ++ | - |
| Fehlerklassen durch Typen (Zustandsautomaten M-003) | o | o | + | - | ++ |
| Lernkurve / Pflegbarkeit durch eine Person (5) | + | ++ | o | + | - |
| Ökosystemreife für das Gebiet „Web-App mit Zeitplanung“ | ++ | + | ++ | ++ | o |

## TypeScript (Node.js)

**Pro**
- Eine Sprache für Backend, Frontend und Assistent-Werkzeuge. Operationsdefinitionen (E-005) lassen sich als Schema (z. B. Zod) einmal beschreiben und liefern Typen, Validierung, JSON-Schema für KI-Werkzeuge und API-Beschreibung.
- Größtes Angebot an Webbibliotheken, offizielles KI-SDK, viel Vorbild-Code (hilft Agenten).
- Schnelle Rückkopplung; Test- und Build-Werkzeuge ausgereift.
- Modulgrenzen lassen sich über Workspaces/Projekte und Linter-Regeln prüfen (QA-003-Architekturtests).
- Passt zu einem Nuxt-/Vue-Frontend oder jedem anderen TS-Frontend (E-004 bleibt offen).

**Contra**
- Mittlere Grundlast (V8); zwei Prozesse kosten spürbar; Abhilfe: gleiches Image, geteilte Pakete, begrenzte Heap-Größe.
- Typen gelten nur zur Übersetzungszeit; Laufzeitprüfung an Rändern (Schema) ist Disziplin.
- Zeitzonen und Zeitrechnung brauchen Sorgfalt (Temporal-API noch jung); RRULE-Bibliotheken haben Schwächen bei Zeitzonen und Pflege ▲.
- Abhängigkeitsbaum (npm) ist groß; Aufwand für Sicherheitsupdates.
- CPU-intensive Arbeit blockiert den Ereignis-Loop (hier wenig relevant, aber Worker-Disziplin nötig).

## Go

**Pro**
- Sehr geringe Grundlast, kleine statische Binärdatei, einfaches Deployment; zwei Prozesse sind kaum ein Problem.
- Einfache Sprache, schnelle Compile- und Testzyklen, wenig „Magie“, gut lesbar für Agenten.
- Starke Standardbibliothek (HTTP, Zeit, Verschlüsselung); ausgereifte Postgres-Anbindung und Auftragsabarbeitung auf Postgres.
- Paketgrenzen (`internal`) und einfache Linter prüfen Abhängigkeitsrichtungen.

**Contra**
- Frontend bleibt TypeScript: zwei Sprachen, doppelte Typen. Die Operationsbeschreibung muss per Codegenerierung in die Gegenrichtung gebracht werden.
- Weniger Ausdrucksstärke für Zustandsautomaten und Fachmodell (keine Summentypen); mehr Boilerplate bei Fehlerbehandlung und Mapping.
- RRULE- und iCalendar-Bibliotheken sind weniger reif als in Python/Java ▲.
- Generische Verträge (Operationsdefinition → mehrere Clients) sind aufwendiger.
- i18n-Ökosystem schmaler.

## Kotlin/Java (schlank)

**Pro**
- Stärkste Werkzeuge für Modulgrenzen (ArchUnit, Modulsystem) und Refactoring; ausgereifte Bibliotheken für iCalendar/RRULE, Zeit, Verschlüsselung, Jobs.
- Starke Typen, Sealed-Klassen für Zustandsautomaten.
- Offizielles KI-SDK; sehr viel Erfahrung mit Webanwendungen und Keycloak (selbst Java).
- Mit nativem Image oder Quarkus/Ktor ist der Speicherbedarf deutlich geringer als bei klassischen Spring-Anwendungen.

**Contra**
- RB-003 benennt den JVM-Stack ausdrücklich als zu begründen; Standard-JVM mit Spring braucht oft 250 MB oder mehr je Prozess, zwei Prozesse sprengen schnell das Budget.
- Native Images: lange Build-Zeiten, eingeschränkte Reflexion, mehr Betriebsaufwand für einen einzelnen Betreiber.
- Frontend bleibt TypeScript: zwei Sprachen.
- Langsamere Rückkopplung als Go/TypeScript; viel Zeremonie.
- chronos-root hat vermutlich genau diese Last verursacht (Key Learning „RAM zu hoch“; Backend-Stack dort nicht in req42 geprüft).

## Python

**Pro**
- Beste RRULE- und iCalendar-Bibliotheken (`dateutil`, `icalendar`, `recurring-ical-events`); Zeitzonenrechnung ausgereift.
- Schnelle Entwicklung, sehr gut für Agenten; offizielles KI-SDK; Pydantic liefert Schema/Validierung und OpenAPI.
- Moderate Grundlast; Postgres-Auftragsabarbeitung vorhanden.

**Contra**
- Zwei Sprachen (Frontend bleibt TypeScript).
- Schwächere statische Garantien; Modulgrenzen nur durch Konvention und Werkzeuge (import-linter), also schwächer für Platz 1.
- Gleichzeitigkeit (async/Worker) und Packaging (virtuelle Umgebungen, Abhängigkeiten) sind Reibung; Speicherbedarf wächst mit den Bibliotheken.
- Zustandsautomaten und Fehlerklassen werden erst zur Laufzeit entdeckt.

## Rust

**Pro**
- Niedrigste Grundlast und Latenz; Budget ist praktisch kein Thema.
- Stärkste Typen: Summentypen modellieren M-003 (Zustände) und Ereignisse direkt; viele Fehlerklassen entfallen zur Übersetzungszeit.
- **Modulgrenzen werden vom Compiler erzwungen** (Arbeitsbereich mit mehreren Crates): Abhängigkeitsrichtungen aus der Bausteinsicht sind nicht umgehbar. Das passt hervorragend zu Platz 1.
- Sicherheitsvorteile (Speichersicherheit, keine Datenrennen).

**Contra**
- Lange Übersetzungszeiten bremsen Rückkopplung, auch bei Agenten; Build-Speicher und -Dauer im CI.
- Steile Lernkurve; Betrieb und Pflege durch eine Person bleiben riskant, Agenten machen häufiger Compiler-Fehler-Schleifen.
- Ökosystem für den Fachbereich dünner: RRULE-/iCalendar-Bibliotheken kleiner und weniger erprobt ▲, i18n-Werkzeuge weniger ausgereift, **kein offizielles Anthropic-SDK** (Stand meines Wissens ▲, Community-Crates oder eigener HTTP-Client).
- Frontend bleibt TypeScript; Operationsbeschreibung nur per Codegenerierung teilbar.
- Operationsbeschreibung → KI-Werkzeuge: möglich (serde/schemars), aber mehr Eigenarbeit.

## Bibliotheken je Sprache (Kandidaten mit Einschätzung)

▲ = Pflegestand und Eignung vor Entscheidung prüfen.

### TypeScript

| Zweck | Kandidat | Einschätzung |
|---|---|---|
| HTTP | Fastify, Hono | Schnell, klein; Fastify reifer, Hono sehr leichtgewichtig |
| Struktur | NestJS | Vorgeprägte Module, aber mehr Magie und Speicher; für Platz 1 prüfenswert, für Budget eher nein |
| Schema/Validierung | Zod, Valibot, TypeBox | Zod verbreitet; TypeBox liefert JSON-Schema direkt (gut für KI-Werkzeuge) |
| Datenbank | Kysely, Drizzle | Typsicheres SQL; Drizzle schlank; Prisma schwerer (eigener Query-Engine-Prozess) |
| Migrationen | Drizzle Kit, dbmate, node-pg-migrate | Alle ausreichend |
| Aufträge auf Postgres | pg-boss, Graphile Worker | Beide etabliert; Graphile Worker eng an Postgres |
| OIDC/Keycloak | openid-client, oauth4webapi, jose | Etabliert; oauth4webapi sehr schlank |
| RRULE/iCal | rrule (rrule.js) ▲, ical.js, rrule-temporal ▲ | rrule.js weit verbreitet, Zeitzonen-Schwächen und Pflege prüfen |
| Zeit | Luxon, Temporal-Polyfill ▲ | Luxon für Zeitzonen reif |
| Web Push | web-push | Etabliert, Pflege moderat ▲ |
| SMTP | Nodemailer | Sehr reif |
| KI | @anthropic-ai/sdk | Offiziell |
| i18n | i18next, Paraglide | Beides etabliert; Paraglide mit Typen für Schlüssel |
| Logging/Metriken | pino, OpenTelemetry | Reif |
| S3 | AWS SDK v3, minio | AWS SDK modular, aber groß; minio leichter |
| Verschlüsselung | `node:crypto`, age (typage) | Standardbibliothek reicht, age für Dateiverschlüsselung |
| Tests/Architektur | Vitest, dependency-cruiser, eslint-plugin-boundaries | Reif |

### Go

| Zweck | Kandidat | Einschätzung |
|---|---|---|
| HTTP | net/http mit chi, Echo | Standardbibliothek reicht fast; chi schlank |
| OpenAPI/Schema | huma | Erzeugt OpenAPI und JSON-Schema aus Typen, gut für Operationsbeschreibung |
| Datenbank | pgx, sqlc | pgx Standard; sqlc erzeugt typsicheren Code aus SQL |
| Migrationen | goose, Atlas | Beide etabliert |
| Aufträge auf Postgres | River | Aktiv, eng an Postgres |
| OIDC | coreos/go-oidc, golang.org/x/oauth2 | Reif |
| RRULE/iCal | teambition/rrule-go ▲, arran4/golang-ical ▲, emersion/go-ical ▲ | Lückenhafter als Python/Java; Zeitzonen und Randfälle prüfen |
| Web Push | webpush-go | Klein, einfach, Pflege prüfen ▲ |
| SMTP | go-mail | Aktiv |
| KI | anthropic-sdk-go | Offiziell |
| i18n | go-i18n, golang.org/x/text | Funktional, weniger Komfort |
| Logging/Metriken | log/slog, OpenTelemetry | Reif |
| S3 | minio-go, AWS SDK v2 | minio-go leichter |
| Verschlüsselung | filippo.io/age | Referenzimplementierung von age |
| Tests/Architektur | testing, testify, arch-go ▲ | Architekturprüfung weniger verbreitet |

### Kotlin/Java

| Zweck | Kandidat | Einschätzung |
|---|---|---|
| Framework | Quarkus, Ktor, Spring Boot | Quarkus/Ktor leichter; Spring am umfassendsten, aber schwer |
| Datenbank | jOOQ, Exposed | jOOQ typsicheres SQL (Lizenzmodell prüfen ▲); Exposed Kotlin-nativ |
| Migrationen | Flyway, Liquibase | Beide Standard |
| Aufträge auf Postgres | JobRunr, db-scheduler | JobRunr komfortabel (Lizenzmodell prüfen ▲), db-scheduler schlank |
| OIDC | Quarkus OIDC, Spring Security, Nimbus | Reif, besonders nah an Keycloak |
| RRULE/iCal | ical4j, lib-recur ▲ | Sehr vollständig, ical4j ausgereift |
| Web Push | nl.martijndwars:web-push ▲ | Etabliert, Pflege prüfen |
| SMTP | Jakarta Mail, Simple Java Mail | Reif |
| KI | anthropic-java | Offiziell |
| i18n | ICU4J, Resource Bundles | Reif |
| Logging/Metriken | SLF4J, Micrometer, OpenTelemetry | Reif |
| S3 | AWS SDK v2 | Groß |
| Verschlüsselung | Tink | Reif |
| Tests/Architektur | JUnit 5, ArchUnit | ArchUnit ist Referenz für Architekturtests |

### Python

| Zweck | Kandidat | Einschätzung |
|---|---|---|
| HTTP | FastAPI, Litestar | Beide mit Schema; FastAPI verbreitet |
| Schema/Validierung | Pydantic | Standard; liefert JSON-Schema |
| Datenbank | SQLAlchemy 2, psycopg 3 | Reif, SQLAlchemy mächtig, aber schwer |
| Migrationen | Alembic | Standard |
| Aufträge auf Postgres | Procrastinate | Postgres-nativ, aktiv ▲ |
| OIDC | Authlib | Reif |
| RRULE/iCal | python-dateutil, icalendar, recurring-ical-events | Beste Abdeckung unter den Kandidaten |
| Web Push | pywebpush ▲ | Funktioniert, Pflege prüfen |
| SMTP | aiosmtplib, stdlib | Reif |
| KI | anthropic | Offiziell |
| i18n | Babel, gettext | Reif |
| Logging/Metriken | structlog, OpenTelemetry | Reif |
| S3 | boto3 (schwer), minio | minio leichter |
| Verschlüsselung | cryptography, pyage ▲ | Reif |
| Tests/Architektur | pytest, import-linter | Architekturprüfung möglich, schwächer |

### Rust

| Zweck | Kandidat | Einschätzung |
|---|---|---|
| HTTP | axum | Verbreitet, Tokio-basiert |
| Schema | serde, schemars, utoipa | Gut, aber mehr Handarbeit für OpenAPI und Werkzeugbeschreibung |
| Datenbank | sqlx, diesel, sea-orm | sqlx prüft SQL zur Übersetzungszeit; Diesel typsicher; Sea-ORM komfortabel |
| Migrationen | sqlx migrate, refinery | Reif |
| Aufträge auf Postgres | apalis ▲, eigener Mechanismus | Ökosystem kleiner; Eigenbau wahrscheinlich |
| OIDC | openidconnect, jsonwebtoken | Reif für Standardfälle |
| RRULE/iCal | rrule ▲, icalendar ▲ | Vorhanden, weniger erprobt, Zeitzonen und Randfälle prüfen |
| Web Push | web-push ▲, web-push-native ▲ | Kleine Projekte, Pflege prüfen |
| SMTP | lettre | Reif |
| KI | Community-Crates oder eigener HTTP-Client (reqwest) ▲ | Kein offizielles SDK nach meinem Stand |
| i18n | fluent-rs, rust-i18n | Funktional, kleiner |
| Logging/Metriken | tracing, OpenTelemetry | Sehr gut |
| S3 | aws-sdk-s3, rust-s3 | Vorhanden |
| Verschlüsselung | rage (age), RustCrypto | Sehr gut |
| Tests/Architektur | cargo test, cargo-deny; Arbeitsbereich mit Crates | Architektur wird durch Crates selbst erzwungen |

## Entscheidungsvorschlag und Spike

**Nach den Gewichten von ADR-001** liegt es nahe: **TypeScript** (Platz 1 und 2: eine Sprache, gemeinsame Schemas; Budget akzeptabel) oder **Rust** (Platz 1 stärker durch Compiler-Grenzen, Platz 3 am besten; dafür Platz 2 und Betrieb schwächer). Go und Python sind Kompromisse, die beide die Zwei-Sprachen-Brücke bezahlen; Kotlin/Java scheidet wegen RB-003 voraussichtlich aus, sofern ein nativer Build nicht als tragbar gilt.

**Vorschlag für einen zeitlich begrenzten Spike (je Kandidat, höchstens ein Tag):** Eine Operation (Termin anlegen) mit Operationsbeschreibung, Postgres-Transaktion, Ereignis festhalten, Worker-Abarbeitung, eine RRULE mit Zeitzone und Sommerzeitwechsel, ein Web-Push-Versand, Speichermessung beider Prozesse im Leerlauf und unter Last. Die Ergebnisse entscheiden die ▲-Punkte.
