---
id: ADR-004
title: Programmiersprache und Laufzeit
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-23
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-002]
quellen: [E-002-sprachwahl-analyse, E-002-spike-kriterien, ADR-001, ADR-002, ADR-003, Spike-Ergebnisse 2026-11-20 bis 2026-11-23 (inkl. Python), Code-Prüfung Python, Bewertungen des Product Owners 2026-11-23]
---

# ADR-004: Programmiersprache und Laufzeit

**Status: freigegeben** vom Product Owner am 2026-11-23 (Entscheidung im Gespräch am selben Tag, siehe „Entscheidung“). Der Entwurf legt das Ergebnis der vier Spikes (TypeScript, Go, Rust, Python) dar. Offene Punkte stehen unter „Offen vor der Freigabe“.

## Kontext
Die Sprache bestimmt, wie gut sich das Ressourcenbudget ([RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md), ADR-002: zwei Prozesse, ADR-003: eigene PostgreSQL-Instanz), die Änderbarkeit (ADR-001 Rang 1) und die Pflege durch eine Person mit Agenten ([RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)) erreichen lassen. Java/Kotlin (Grundspeicher) hat der Product Owner ausgeschlossen, Python zunächst ebenfalls (Mehrverbrauch ohne ausreichenden Vorteil gegenüber TypeScript, [Analyse](E-002-sprachwahl-analyse.md)). Auf seinen Wunsch wurde Python am 2026-11-23 **nachträglich** mit demselben Verfahren gebaut und gemessen, die Vorentscheidung bleibt dokumentiert. Für **TypeScript** (Node.js 22, Fastify, Kysely, Zod/TypeBox), **Go** (chi, huma, pgx, sqlc) **Rust** (axum, sqlx, serde, utoipa) und **Python** (FastAPI, Pydantic v2, SQLAlchemy 2 asynchron, psycopg 3, uvicorn) hat je ein Agent denselben Durchstich gebaut ([V-1](../../../spikes/e-002/common/V-1-aufgabenbeschreibung.md)), gemessen nach den vorab festgelegten [Kriterien](E-002-spike-kriterien.md).

**Bedingungen und Grenzen des Ergebnisses:**
- **Ein Lauf je Sprache**, keine Wiederholung. Unterschiede von wenigen Punkten sind kein Beleg.
- Alle Agenten waren **Sonnet 5.5** (nicht Opus, wie geplant), weil das Nutzungslimit des Kontos erreicht war. Die Aussage gilt für Sonnet-Agenten.
- Die Agenten arbeiteten **12 bis 34 Minuten** (Python 17 Minuten bis Phase 1) statt der geplanten 8 Stunden. Die Spikes sind klein (minimaler Durchstich).
- Messung in einer VM (12 GB, 8 CPUs, amd64), Werte nur untereinander vergleichbar. Bei Python liefen die Messungen M-7 und M-12 mit lokal installiertem `uv` (im Container wären es 14,5 s und 8,5 s wegen des Docker-Starts); die Einzelzeiten der Aufgaben hat der Python-Agent nachträglich rekonstruiert.
- Die Aufgabenbeschreibung V-1 hatte eine **Lücke**: Der Endpunkt `GET /api/v1/push/vapid-public-key` stand nur in der Testseite des manuellen Tests K3, nicht in V-1. Nur der TypeScript-Agent hat ihn gebaut. Der Test K3 wurde angepasst (Schlüssel in der Adresse), K3 bestand bei TypeScript, Go und Rust; für Python steht K3 noch aus.
- Spike-Kandidaten wurden mit Bibliotheksständen von November 2026 gebaut; Pflegestand und Sicherheitsmeldungen ändern sich laufend.

## Optionen und Ergebnis

**Abnahme (alle Gruppen grün bei allen vier):** S-1 bis S-3 (Operationen, Team-Baum, Transaktion, Verlauf, Rückgängig), K2 (RRULE, 29 Fälle), K4 (Keycloak), K5 (Worker-Absturz), K6 (KI), M-14, M-15, S-10 (Frontend-Brücke), Phase 2 (neue Operation). K3 (Web Push in Firefox und Chrome): bei TypeScript, Go und Rust bestanden, geprüft vom Product Owner; Python noch offen. K7: Docker Compose statt k3s, vom Product Owner als gleichwertig anerkannt.

**Messwerte** (Median aus 3 Läufen, ein Lauf = 10 min Last, 20 Anfragen/s):

| Messgröße | TypeScript | Go | Rust | Python |
|---|---|---|---|---|
| Speicher Leerlauf, Web + Worker (M-1) | 88,7 MiB | 16,4 MiB | 12,0 MiB | 212,2 MiB |
| Speicher Spitze unter Last (M-2) | 108,5 MiB | 22,9 MiB | 12,7 MiB | 212,8 MiB |
| CPU Mittel / Spitze (M-3) | 200 / 1428 mCPU | 55 / 181 mCPU | 38 / 103 mCPU | 281 / 1883 mCPU |
| Latenz p50 / p95 / p99 (M-4) | 3,6 / 30,3 / 36,1 ms | 4,5 / 21,4 / 55,0 ms | 4,9 / 31,3 / 73,7 ms | 15,0 / 58,0 / 93,7 ms |
| Startzeit (M-5) | 1,72 s | 0,72 s | 0,80 s | 4,31 s |
| Image (M-6) | 71,6 MB | 7,4 MB | 40,5 MB | 85,5 MB |
| PostgreSQL-Verbindungen (M-13) | 19 | 21 | 20 | 27 |
| Rückkopplung (M-7) | 5,0 s | 0,7 s | 1,7 s | 2,7 s |
| Abhängigkeiten im Produktions-Build (M-8) | 117 Pakete | 41 Module | 375 Crates | 59 Pakete |
| Hohe Schwachstellen (M-8) | 0 | 0 | 0 (2 mittlere oder unbewertete, 2 „unmaintained“) | 0 (`pip-audit`: keine bekannten) |
| Eigenbau-Anteil (M-9) | 4,9 % | 7,0 % | 3,1 % | 9,2 % (152 von 1657 Zeilen, ohne Tests) |
| Zeit bis Phase 1 / Korrekturschleifen (M-10) | 12 min / 3 | 19 min / 5 | 34 min / 6 | 17 min / 3 |
| Berührte Dateien für neue Operation (M-11) | 3 | 1 | 1 | 3 (davon 1 reine N-1-Änderung) |
| Architekturverstoß erkannt (M-12) | ja, 1,3 s | ja, 0,07 s | ja, 0,01 s | ja, 0,18 s |
| Doppelversuche nach Worker-Absturz (K5) | 1 | 8 | 4 | 16 |

Alle Kandidaten bleiben unter dem K.-o.-Wert K1 (512 MiB, 500 mCPU). Python liegt bei M-1 (Grenzwert 200 MiB) mit 212 MiB schon im Leerlauf über der Wertungsgrenze und erhält dort 0 Punkte. Bei M-8 sind die Einheiten verschieden (Paket, Modul, Crate); der Vergleich ist grob.

**Bewertung durch den Product Owner (1 bis 5):**

| | TypeScript | Go | Rust | Python |
|---|---|---|---|---|
| Q-1 Verständlichkeit | 5 | 4 | 5 | offen |
| Q-2 Vertrautheit mit der Sprache | 4 | 2 | 4 | offen |
| Q-3 Fehlermeldungen, Debugging | 4 | 4 | 4 | offen |
| Q-4 Pflegestand der Bibliotheken | 3 | 3 | 2 | offen (Vorschlag 4: `python-dateutil` 4.0.0 11/2026, `authlib`, `pyjwt`, offizielles SDK frisch; Abzug für `http-ece`, 27 Monate ohne Release) |
| Q-5 Frontend-Brücke | 4 | 4 | 5 | offen |

**Gesamtpunkte (0 bis 100), nach Rank-Order-Centroid-Gewichten aus ADR-001, mit drei Gewichtungen:**

| Rechnung | TypeScript | Go | Rust | Python (vorläufig) |
|---|---|---|---|---|
| Rangfolge ADR-001 (46/26/16/9/4) | 87,0 | 86,1 | **90,8** | 71,2 |
| Gleiche Gewichte | 85,6 | 86,4 | **89,7** | 70,5 |
| Ressourcen an Rang 1 | 83,8 | 87,4 | **90,5** | 62,4 |

Python ist **vorläufig** gerechnet: Q-1 bis Q-5 stehen noch aus und zählen als neutral (3), K3 wird als bestanden angenommen. Selbst mit der günstigsten Annahme (Q-Werte wie bei TypeScript, Q-4 gleich 4) erreicht Python höchstens 79,0 / 76,9 / 67,1 Punkte und läge damit hinter allen drei anderen.

Rust liegt in allen Rechnungen vorn, der Vorsprung (3,1 bis 3,8 Punkte) erfüllt die Entscheidungsregel des Kriteriendokuments (gleicher Sieger **und** mindestens 5 Punkte) **nicht**. Es ist ein Befund, keine Entscheidung. Ein Q-Punkt bei Q-4 verschiebt das Ergebnis um etwa 1,3 Punkte.

**Stärken und Schwächen je Kandidat:**
- **TypeScript:** Schnellste Umsetzung (12 min), wenigste Korrekturschleifen, gute Lesbarkeit, offizielles KI-SDK, kleine Abhängigkeitsmenge (117). Höchster Ressourcenverbrauch (CPU-Spitze 1428 mCPU, 109 MiB), RRULE-Bibliothek 36 Monate ohne Release.
- **Go:** Kleinstes Image, wenigste Abhängigkeiten (41 Module), schnellste Rückkopplung, offizielles KI-SDK, breite Maintainer-Basis bei OIDC. Schwächster Wert bei Q-2 (Vertrautheit des Product Owners), höchster Eigenbau (7 %), RRULE-Bibliothek 46 Monate ohne Release, Web Push 22 Monate.
- **Python:** Beste Bibliotheken (RRULE `python-dateutil`, `authlib`, `pyjwt`, offizielles KI-SDK, alle mit aktuellen Releases), sehr gut lesbar, elegante Operationsbeschreibung (`@operation` mit Pydantic-Typen, Vorschau durch Rollback ohne Zusatzcode), wenige Abhängigkeiten (59) und keine bekannten Schwachstellen, schnelle Umsetzung (17 min, 3 Schleifen). Aber höchster Speicherbedarf (212 MiB im Leerlauf, Wertung 0 Punkte), höchste Latenz und Startzeit (4,3 s), meiste PostgreSQL-Verbindungen (27), Eigenbau-Anteil 9,2 %. **Code-Prüfung:** (1) Die RRULE-Ausdehnung läuft synchron in der einzigen Ereignisschleife: eine nie treffende Regel blockiert das Web rund 4,5 s (gemessen), (2) der Worker gibt beim Start alle Sperren frei und setzt einen einzigen Worker-Prozess voraus (16 Doppelversuche, bei Rolling Update in k3s riskant), (3) `ai.ask` hält die Datenbanktransaktion während des KI-Aufrufs offen (Pool-Erschöpfung bei Last).
- **Rust:** Geringster Speicher und CPU, beste Frontend-Brücke (Vorschau und Schreibmerkmal in den Typen), kleinster Eigenbau (3,1 %). Größte Abhängigkeitsmenge (375 Crates), schwächster Pflegestand (Q-4: `rrule` und `web-push` über 18 Monate ohne Release, `chrono-tz` archiviert, kein offizielles KI-SDK), längste Umsetzung (34 min, 6 Schleifen), lange Bauzeit und viel Plattenplatz (ungemessen).

## Entscheidung (PO, Gespräch 2026-11-23)
1. **Sprache und Laufzeit: Rust** für Web und Worker, mit den Frameworks axum, sqlx, serde, utoipa. Gründe: bester Wert bei Ressourcen (RB-003, Rang 3) und Bedienbarkeit (Rang 2), kleinster Eigenbau, gleichauf bei Änderbarkeit (Rang 1: TypeScript 8,6, Rust 8,4, Go 7,9 von 10), und der Product Owner hat die Lesbarkeit (Q-1) und die Frontend-Brücke (Q-5) am besten bewertet. Der Vorsprung ist klein (3,1 bis 3,8 Punkte, Regel verlangt 5): Die Entscheidung stützt sich auf den Befund, nicht auf die Entscheidungsregel. **TypeScript bleibt die naheliegende Alternative**, wenn Lieferkette und Abhängigkeitsmenge höher gewichtet werden als Ressourcen.
2. **Python scheidet bestätigt aus** (Vorentscheidung des Product Owners): Speicher, CPU, Latenz und Startzeit liegen weit hinter den anderen, und das Ressourcenbudget (RB-003) ist die Randbedingung, bei der Python nicht mithalten kann. Die Stärken von Python (Bibliotheken, Lesbarkeit) wiegen das bei Rang 3 (Ressourcen) und Rang 2 (Bedienbarkeit) nicht auf. K3 und Q-1 bis Q-5 für Python wurden **nicht erhoben**.
3. **Kein Wiederholungslauf mit Opus.** Die Entscheidung gilt auf dem Befund mit Sonnet-Agenten, ein Lauf je Sprache. Zeit, Korrekturschleifen und Eigenbau-Anteil hängen vom Agenten ab und sind nur mit Vorbehalt zu lesen.
4. **RRULE (Rust): `rrule` 0.14 behalten**, hinter der Schnittstelle `expand` isolieren und mit einem **Differenztest gegen python-dateutil** (zufällige Regeln, mehrere Zonen, Jahrzehnte) absichern. Der Eigenbau auf `jiff` (298 Zeilen, 29/29 Katalogfälle, Eigenbau-Anteil 12,5 %) ist **Plan B**, der Port als geschlossene Pull-Request #151 im Upstream ist eine weitere Option.
5. **Web Push (Rust): `web-push-native` 0.5.** Der K3-Test im Browser (Firefox und Chrome) ist am 2026-11-23 bestanden (Product Owner); `web-push` 0.11 entfällt. Die Bibliothek steht hinter der Kanal-Schnittstelle (austauschbar). Bedingungen aus dem Experiment: Längenprüfung der VAPID-Schlüssel (Panic-Falle in `jwt-simple`), Behandlung von 404/410 (Abo löschen, nicht wiederholen), `Retry-After`, gemeinsamer HTTP-Client.
6. **Sicherheitsmeldungen:** `cargo audit` oder `cargo-deny` ist ein **Pflichtschritt der Pipeline** (wie `arch-check`) mit einer Liste begründeter Ausnahmen. `url` ist zu aktualisieren, `rsa` 0.9.10 (nur öffentliche Signaturen, keine Zeitangriffs-Fläche) und `crypto-bigint` 0.5.5 sind begründete Ausnahmen, `chrono` und `chrono-tz` „unmaintained“ werden beobachtet. Monatliche Prüfung.

## Offen nach der Freigabe (Umsetzung)
1. **Differenztest für RRULE** gegen python-dateutil als erste Aufgabe der Umsetzung (Entscheidung 4), nicht Voraussetzung der Freigabe.
2. **Lücke in V-1** (Endpunkt für den öffentlichen VAPID-Schlüssel) ist für die Anwendung zu schließen: Die Schlüsselausgabe an den Browser gehört in die Spezifikation von Web Push (FA, E-004).

Entscheidungen, die diese Auswahl voraussetzen, stehen im nächsten Abschnitt. Das Ergebnis der Experimente E-002a (`jiff` statt `rrule`: 298 Zeilen Eigenbau, 29/29 Katalogfälle, Eigenbau-Anteil 12,5 %, Rust-Vorsprung fast aufgezehrt) und E-002b (`web-push-native`: OpenSSL, `web-push`, `native-tls`, `hyper-tls` und `ece` aus dem Baum, aber nur 12 Crates weniger, 375 auf 363, alle Sicherheitsmeldungen bleiben, Eigenbau-Anteil 3,1 auf 3,8 %, Einzelmaintainer, 5 Tests, Panic-Falle) bleibt als Belege für die Entscheidungen 4 und 5 erhalten.

## Folgen
- **Leichter:** Ressourcenbudget (gemessen 12,7 MiB für Web und Worker zusammen unter Last, bei TypeScript 108,5 MiB), kleine Images, starke Typisierung der Operationsschicht und Frontend-Brücke (K-006), Agenten finden Fehler früh über den Übersetzer.
- **Schwerer:** Größere Abhängigkeitsmenge und Lieferkette (375 Crates), Sicherheitsmeldungen und Pflegestand der Bibliotheken laufend prüfen (neue Aufgabe für den Betreiber, [RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)), längere Bauzeit und Plattenbedarf in Entwicklung und Pipeline (Build-Cache einplanen), Web-Push-Bibliothek und RRULE-Pflege als Dauerthema.
- **Risiken (Kapitel 11):** Neues Risiko „Bibliotheken ohne Pflege in kritischen Pfaden“ (RRULE, Web Push, Zeitzonen) mit Maßnahmen: Isolation hinter Schnittstellen, Differenztests, Plan B (`jiff`), regelmäßige Prüfung. R-A1 (Budget gegen Funktionsumfang) sinkt.
- **Bindet oder gibt frei:** siehe nächster Abschnitt.

## Was an dieser Entscheidung hängt
Entscheidungen aus [Kapitel 9](01-offene-entscheidungen.md), die mit E-002 frei oder konkreter werden:

| Entscheidung | Wie E-002 sie berührt |
|---|---|
| E-004 Frontend-Ansatz | Direkt abhängig (Vorab: E-002). Der Spike lieferte nur die typisierte Brücke (TypeScript-Client mit generierten Typen), keine Oberfläche. Mobil zuerst, Web Push (K3 bestanden), i18n offen. |
| E-005 Operationsschicht | Abhängig (Vorab: E-001, E-002). Alle vier Spikes erzeugen API, Validierung, KI-Werkzeugschema und Brückentypen aus **einer** Operationsbeschreibung (bei Python mit Pydantic und einem Dekorator am knappsten); das ist ein Beleg für die Option „eine Definition erzeugt alles“. Die konkrete Form ist sprachabhängig. |
| E-008 Keycloak und Gäste | Zurückgestellt bis E-002 und E-004. Spike: Authorization Code mit PKCE und Token-Prüfung funktionierten (K4 bei allen vier). Bibliothekswahl hängt an der Sprache (Rust: `openidconnect`, `jsonwebtoken`). |
| E-009 KI-Anbindung | Abhängig von E-005. Rust hat kein offizielles SDK (TypeScript, Go und Python schon); die Anbieterschnittstelle (RB-011) bleibt ohnehin nötig. |
| E-016 Teststrategie und Architekturtests | Direkt abhängig. Der Spike zeigt, dass der Architekturverstoß (S-9) in allen vier Sprachen automatisch erkannt wird (Millisekunden bis Sekunden). Werkzeug sprachabhängig. |
| E-006 Ereignisse und Zustellung | Bereits entschieden (Outbox in der Datenbank). Der Spike hat die Umsetzung ohne Bibliothek bestätigt (Tabelle, `SKIP LOCKED`, Lease). Idempotenz und Wiederholung sind sprachunabhängig. Der Python-Spike zeigt die Grenze des einfachen Verfahrens: Gibt der Worker beim Start alle Sperren frei, ist das nur mit einem Worker-Prozess sicher. |
| E-013 Serien (Vorkommen materialisieren) | Entschieden. Die RRULE-Bibliothek ist der kritische Punkt (siehe „Offen vor der Freigabe“). |
| E-010, E-011, E-012, E-014, E-017 | Entschieden. Betroffen sind nur die Bibliotheken (S3-Client, SMTP `lettre`, Logging, Importwerkzeug über die Operationsschicht). |
| [ADR-003](ADR-003-datenbank-postgresql.md) | Migrationswerkzeug „folgt aus E-002“: bei Rust `sqlx` (migrate) oder ein eigenes Werkzeug. Offen. |
| [K-007](../08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md) | Format der Übersetzungsdateien (JSON oder PO) und Plural-/Datumsformate „nach E-002“. |
| [ADR-001](ADR-001-prioritaet-der-qualitaetsziele.md) | Folge „bei Zielkonflikt gewinnt die modularere Lösung“ wird mit der Sprache konkret (Modulgrenzen, Abhängigkeitsregel als Test). |

## Wann überprüfen?
- Wenn die Messung im echten Betrieb (nicht in der VM) das Budget verfehlt oder die Abhängigkeitsmenge zum Betriebsrisiko wird (häufige Sicherheitsmeldungen ohne Korrektur).
- Wenn die kritischen Bibliotheken (RRULE, Web Push, OIDC) in Rust ausfallen und der Ersatz mehr Eigenbau bedeutet als vorgesehen.
- Wenn sich die Prioritäten aus ADR-001 ändern (etwa Änderbarkeit durch viele Mitwirkende wichtiger als Ressourcen).
- Wenn ein Wiederholungslauf der Spikes (andere Modellstufe oder mehrere Läufe) den Abstand deutlich verändert.
