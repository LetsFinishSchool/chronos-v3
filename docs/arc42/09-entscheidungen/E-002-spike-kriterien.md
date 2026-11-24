---
title: E-002 Spike-Kriterien und Metriken (Vorschlag)
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [Gespräch mit dem Product Owner 2026-11-20, ADR-001, ADR-002, ADR-003, E-002-sprachwahl-analyse, req42 QA-001..QA-010, RB-003]
---

# E-002: Spike-Kriterien und Metriken (Vorschlag)

**Zweck:** Vor dem Spike festlegen, woran die Kandidaten **TypeScript**, **Go** und **Rust** gemessen werden, damit das Ergebnis nicht nachträglich zurechtgebogen wird. Python und Java/Kotlin sind ausgeschieden (Begründung des Product Owners siehe [Analyse](E-002-sprachwahl-analyse.md#vorentscheidung-des-product-owners)). Die Spikes setzen **Agenten** um. Die Festlegungen aus dem Gespräch vom 2026-11-20 sind in Abschnitt 8 festgehalten (Entwurf, Freigabe des Product Owners steht aus).

## 1. Rahmen und Fairness

| Punkt | Vorschlag |
|---|---|
| Zeitbox | **8 Stunden Wall-Clock** je Agent-Spike, alle drei **parallel**. Aufgabenumfang siehe 2. Was nicht fertig wird, zählt als „nicht erreicht“ und wird bewertet, nicht verlängert. |
| Reihenfolge | Entfällt, weil parallel. Jeder Agent arbeitet in einem **eigenen Worktree** und sieht weder Code noch Zwischenstände der anderen. |
| Vorgehen | Drei Agenten, **gleiches Modell, gleiche Aufgabenbeschreibung**, kein Eingriff des Menschen während des Laufs (Rückfragen werden einheitlich beantwortet und protokolliert). Jede Schleife (Fehler, Korrektur) und der Tokenverbrauch werden gezählt. |
| Frameworks | Vorab festgelegt, idiomatisch und schlank, kein Wechsel während des Spikes. Vorschlag: TypeScript: Fastify, Kysely, Zod/TypeBox; Go: chi, huma, pgx, sqlc; Rust: axum, sqlx, serde, utoipa. |
| Ort | Eigener Zweig bzw. Verzeichnis `spikes/e-002-<sprache>`, **nicht** im Hauptzweig; Ergebnis nur als Protokoll im Wiki. |
| Umgebung | Gleicher Rechner und gleiche Container-Grenzen (z. B. 1 vCPU gesamt), gleiche PostgreSQL-Konfiguration für alle, Produktionsmodus (Release-Build). Zielplattform und Messplattform: **amd64**. |
| Messung | **Nicht durch den Agenten selbst:** ein gemeinsames, sprachunabhängiges Messskript und eine gemeinsame Abnahmesuite (siehe 2a) laufen gegen jeden Kandidaten. Je Metrik 3 Läufe, Median; dasselbe Werkzeug für alle (Container-Speicher als `working set`). PostgreSQL wird gleich konfiguriert und **nicht** als Unterscheidungsmerkmal gewertet; für das Budget reserviert: 256 MiB. |
| Dokumentation | Pro Kandidat ein Protokoll nach Vorlage (Abschnitt 7). |

## 2. Spike-Aufgabe (für alle gleich)

| Nr. | Aufgabe | Deckt ab |
|---|---|---|
| S-1 | **Zwei Operationen** (Termin anlegen, Termin absagen) einmal beschreiben (Name, Parameter, lesend/schreibend, Vorschau). Aus der Beschreibung entstehen API-Endpunkt, Validierung und KI-Werkzeugschema. | E-005, QA-003 c |
| S-2 | **Team-Baum:** Abfrage aller Mitglieder oberhalb und unterhalb (3 Ebenen), Berechtigungsprüfung an einer Stelle. | M-001, M-002 |
| S-3 | **Transaktion:** Zustandsänderung, Verlauf mit Vorher-Zustand und Bündel-ID, Ereignis mit Auslöser und Korrelations-ID in einer Transaktion; „Absage rückgängig machen“. | K-003, K-004 |
| S-4 | **Worker:** Ereignis aus der Datenbank abarbeiten, Zustellung an einen Mock-Kanal (50 ms), echten Web Push und E-Mail an einen lokalen Mailserver; Wiederholung begrenzt, Ersatzkanal, höchstens eine Zustellung je Empfänger und Kanal. | K-003, QA-004 |
| S-5 | **Serie:** Wochentermin 18:00 in Europe/Berlin über den Sommerzeitwechsel; Testkatalog (siehe K.-o. 2). | FA-014 |
| S-6 | **Anmeldung:** OIDC-Login gegen ein **lokales Keycloak im Container** (Wegwerfinstanz, vorbereitet), Authorization Code mit PKCE, Sitzung. | RB-002 |
| S-7 | **KI:** Ein echter Aufruf des Anthropic-API mit dem Werkzeugschema aus S-1; Kosten werden als Posten erfasst. Der Zugang kommt **von außen über die Umgebung**, nie ins Repository ([RB-008](../../req42/07-randbedingungen/RB-008-keine-geheimnisse-im-repository.md)); eigenes Kostenlimit für den Spike. | FA-015, RB-010 |
| S-8 | **Last:** Skript mit 50 gleichzeitigen Verbindungen, 20 Anfragen/s (90 % lesend, 10 % schreibend) über 10 min, parallel 2000 Zustellungen im Worker. Gleiches Skript für alle. | QA-001, QA-008 |
| S-9 | **Architekturregel:** Absichtlicher Verstoß (Fachbereich importiert einen Kanal) wird versucht. | QA-003 |
| S-10 | **Frontend-Brücke:** Aus der Operationsbeschreibung die Typen für einen minimalen Client (eine Seite) gewinnen. | E-004 |

## 2a. Vorbereitung (vor dem Start, sprachunabhängig)

| Nr. | Artefakt | Zweck |
|---|---|---|
| V-1 | Schriftliche Aufgabenbeschreibung S-1 bis S-10 mit festen Schnittstellen (HTTP-Verträge) | Gleiche Aufgabe, kein Spielraum bei der Auslegung |
| V-2 | **Abnahmesuite** als HTTP-Blackbox-Tests inkl. RRULE-Katalog (≥ 20 Fälle) und Zuverlässigkeitstest (`kill -9`) | Prüft K2 bis K6 und M-14 unabhängig vom Agenten |
| V-3 | **Lastskript** (S-8) und **Messskript** (Speicher, CPU, Latenz, Startzeit, Image, Verbindungen) | Gleiche, nicht vom Agenten beeinflusste Messung |
| V-4 | Container-Umgebung: PostgreSQL (feste Konfiguration), Mailpit, Keycloak (Wegwerfinstanz mit Testrealm), Mock-Kanal | Gleiche Umgebung |
| V-5 | **Agentenbriefing:** Aufgabe, Frameworkvorgabe, Zeitbox, Regeln (keine Geheimnisse ins Repository, Protokoll führen, nichts außerhalb des Worktrees ändern) | Gleiche Ausgangslage |
| V-6 | Bereitstellung des Anthropic-Zugangs mit Kostenlimit über die Umgebung | S-7 |

Die Erstellung von V-1 bis V-6 ist Aufwand vor dem Spike und gehört nicht in die Zeitbox der Agenten.

## 3. K.-o.-Kriterien (müssen erfüllt sein)

| Nr. | Kriterium | Bestanden, wenn |
|---|---|---|
| K1 | **Budget** | Web + Worker zusammen unter Last (S-8) höchstens **512 MiB** Peak-Speicher und **500 mCPU** im Mittel. (Rechnung: 1024 MiB − 256 MiB PostgreSQL − 256 MiB Reserve.) |
| K2 | **RRULE korrekt** | 100 % eines vorab festgelegten Katalogs von ≥ 20 Fällen: u. a. `BYDAY`, `BYSETPOS`, `BYMONTHDAY=-1`, `INTERVAL`, `COUNT`/`UNTIL`, `EXDATE`, Sommerzeitwechsel in beide Richtungen, ungültige Regeln werden abgelehnt. Eine eigene Implementierung von mehr als 100 Zeilen gilt als nicht bestanden. |
| K3 | **Web Push** | Echte Zustellung an Chrome und Firefox (Desktop), VAPID und Nutzlastverschlüsselung ohne Eigenbau. |
| K4 | **OIDC/Keycloak** | Login und Abmeldung funktionieren; Token-Prüfung ohne Eigenbau. |
| K5 | **Zuverlässigkeit** | Nach `kill -9` des Workers während des Versands: kein verlorenes Ereignis und höchstens eine Zustellung je Empfänger und Kanal (Test mit 100 Ereignissen). |

**Klarstellung K5:** Exakt-einmal-Zustellung gibt es bei externen Kanälen nicht. Geprüft wird: **kein Verlust**, und jede Zustellung ist **wirksam genau einmal** (Idempotenzschlüssel `<Ereignis>:<Empfänger>:<Kanal>`, der Mock-Kanal dedupliziert). Doppelte Versuche werden gezählt und berichtet (M-14), nicht als Durchfall gewertet. Bitte bestätigen.
| K6 | **KI-Anbindung** | Werkzeugaufruf funktioniert mit dem Schema aus S-1; ohne offizielles SDK höchstens 100 Zeilen Eigencode. |
| K7 | **Auslieferung** | Reproduzierbarer Container-Build, läuft als Web und als Worker (Start-Variante) auf k3s oder einem gleichwertigen lokalen Cluster. |

Wer ein K.-o.-Kriterium nicht erfüllt, scheidet aus, unabhängig von der Punktzahl.

## 4. Metriken

### Quantitativ

Normierung: Zielwert = 10 Punkte, Grenzwert = 0 Punkte, dazwischen linear. Besser als Ziel bleibt 10.

| Nr. | Metrik | Messung | Ziel | Grenze |
|---|---|---|---|---|
| M-1 | Speicher im Leerlauf (Summe Web + Worker) | `working set`, 5 min nach Start | ≤ 40 MiB | 200 MiB |
| M-2 | Speicher unter Last (Peak, Summe) | S-8 | ≤ 100 MiB | 400 MiB |
| M-3 | CPU unter Last (Mittel, Summe) | S-8 | ≤ 100 mCPU | 500 mCPU |
| M-4 | Latenz Lese-/Schreib-Operation (p95; p99 wird berichtet) | S-8 | ≤ 50 ms | 300 ms |
| M-5 | Startzeit bis bereit (Kaltstart, Web) | Zeit bis Gesundheitsprüfung | ≤ 1 s | 10 s |
| M-6 | Größe des Container-Images | Bytes | ≤ 50 MB | 400 MB |
| M-7 | Rückkopplung: Änderung → übersetzt + Tests laufen (inkrementell) | Sekunden, Median von 5 | ≤ 5 s | 60 s |
| M-8 | Abhängigkeiten direkt + transitiv; bekannte Schwachstellen | Werkzeug der Sprache | ≤ 50, 0 offene hohe | 500, ≥ 3 hohe |
| M-9 | Eigenbau-Anteil | Zeilen, die Bibliothekslücken füllen, ÷ Zeilen gesamt | ≤ 2 % | 15 % |
| M-10 | Aufwand des Agenten | Wall-Clock bis S-1..S-7 fertig und Zahl der Korrekturschleifen (Tokenverbrauch wird berichtet, nicht bewertet) | ≤ 2 h, ≤ 10 | 8 h, ≥ 40 |
| M-11 | Neue Operation: berührte Dateien/Module (Test: „Termin verschieben“ ergänzen), KI-Werkzeug entsteht automatisch (ja = 10, nein = 0 Punkte Anteil) | Zählung | 1 Stelle | 6 Stellen |
| M-12 | Architekturverstoß (S-9) automatisch erkannt | ja/nein und Sekunden bis zur Meldung | ja, ≤ 10 s | nein |
| M-13 | PostgreSQL-Verbindungen bei Last (Summe beider Prozesse) | `pg_stat_activity` | ≤ 6 | 30 |
| M-14 | Robustheit des Workers | Bestandene Fälle ÷ Fälle (kill -9, Kanalfehler, Doppelzustellung, Neustart, vergiftetes Ereignis) | 100 % | 60 % |
| M-15 | Korrelations-ID | Stellen im Code, an denen sie von Hand durchgereicht wird; Stichprobe von 10 Zustellungen vollständig rückführbar | 0 bis 1 Stelle, 10/10 | 10 Stellen, 5/10 |

### Qualitativ (Skala 1 bis 5, bewertet vom Product Owner anhand des fertigen Spike-Codes, Begründung in einem Satz)

| Nr. | Kriterium | Anker 1 | Anker 5 |
|---|---|---|---|
| Q-1 | Verständlichkeit des Codes für den Product Owner | Auch nach 30 min nicht nachvollziehbar | Nach 15 min Ablauf und Struktur klar |
| Q-2 | Vertrautheit und Sicherheit im Umgang mit der Sprache (Selbsteinschätzung nach dem Lesen des Spike-Codes) | Würde ich allein nicht pflegen | Würde ich allein pflegen und erweitern |
| Q-3 | Fehlermeldungen und Debugging (Compilerfehler, Laufzeitfehler, Logs) | Rätselhaft, lange Suche | Meist unmittelbar Ursache und Ort erkennbar |
| Q-4 | Pflegestand der kritischen Bibliotheken (RRULE, Web Push, OIDC, Jobs, SDK) | Mehrere ohne Release > 12 Monate oder einzelner Maintainer | Alle gepflegt, ≥ 2 Maintainer, Releases < 12 Monate |
| Q-5 | Frontend-Brücke (S-10) | Typen von Hand doppelt gepflegt | Typen geteilt oder fehlerfrei generiert |

## 5. Gewichtung (aus ADR-001)

Die Metriken werden den fünf Qualitätszielen zugeordnet. Die Gewichte der Ziele folgen aus der Rangfolge nach dem Rank-Order-Centroid-Verfahren (Rang 1 bis 5: 46 %, 26 %, 16 %, 9 %, 4 %), damit die Rangfolge nicht durch freihändige Zahlen verzerrt wird. Innerhalb eines Ziels zählen die Metriken gleich; Q-Werte werden auf 0 bis 10 skaliert (1 = 0, 5 = 10).

| Ziel (Rang, Gewicht) | Metriken |
|---|---|
| Änderbarkeit (1, 46 %) | M-7, M-8, M-9, M-10, M-11, M-12, Q-1, Q-2, Q-4 |
| Bedienbarkeit mobil, Zugang (2, 26 %) | M-4, M-5, Q-5 |
| Ressourceneffizienz (3, 16 %) | M-1, M-2, M-3, M-6, M-13 |
| Benachrichtigung (4, 9 %) | M-14 |
| Nachvollziehbarkeit (5, 4 %) | M-15, Q-3 |

**Anmerkung:** Dass die Rangfolge Änderbarkeit mit 46 % am stärksten gewichtet, entspricht ADR-001. Die dort nicht enthaltene Betriebsfähigkeit durch eine Person ([RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)) ist über M-10, Q-1 und Q-2 in Änderbarkeit enthalten (vgl. [Z-005](../../req42/01-ziele/Z-005-schlank-betreiben-und-leicht-weiterentwickeln.md)).

## 6. Auswertung

1. K.-o.-Kriterien prüfen; wer scheitert, scheidet aus.
2. Punktzahl je Kandidat = Summe über Ziele (Gewicht × Mittelwert der Punkte der Metriken des Ziels).
3. **Sensitivitätsprüfung:** Ergebnis zusätzlich mit gleichen Gewichten (je 20 %) und mit Ressourceneffizienz an Rang 1 berechnen.
4. **Entscheidungsregel:** Gewinnt derselbe Kandidat in allen drei Rechnungen mit mindestens 5 Punkten (von 100) Vorsprung, wird er vorgeschlagen. Sonst ist das Ergebnis ein Befund, über den der Product Owner entscheidet (Gründe im ADR).
5. Ergebnis als ADR-004 festhalten; das Protokoll liegt im Wiki.

## 7. Protokollvorlage je Kandidat

Kandidat, Datum, Reihenfolge, verwendete Bibliotheken mit Versionen, K1 bis K7 (bestanden ja/nein mit Beleg), Rohwerte M-1 bis M-15 (3 Läufe, Median), Q-1 bis Q-5 mit Begründung, Stundenlog, nicht erreichte Aufgaben, Auffälligkeiten (insbesondere Bibliotheken ▲ aus der [Analyse](E-002-sprachwahl-analyse.md) mit Befund).

## 8. Festlegungen aus dem Gespräch (2026-11-20, Entwurf)

| Frage | Festlegung |
|---|---|
| Schwellenwerte | Wie vorgeschlagen (K1: 512 MiB und 500 mCPU für Web + Worker unter Last; Ziel- und Grenzwerte M-1 bis M-15 unverändert). |
| Zeitbox | 8 Stunden Wall-Clock je Agent, alle drei parallel. |
| Frameworks | Wie vorgeschlagen und vorab festgelegt. |
| Zielplattform | amd64. |
| Zugänge | Anthropic vorhanden; keine Keycloak-Testinstanz, daher lokales Keycloak im Container (S-6). |
| Gewichtung | Rank-Order-Centroid (46 / 26 / 16 / 9 / 4 %). |
| Frontend-Brücke | Zählt schon in E-002 (Q-5, S-10). |
| Umsetzung | Durch Agenten, parallel und isoliert; Messung und Abnahme unabhängig vom Agenten (Abschnitt 1 und 2a). |

## 9. Nächste Schritte

1. Vorbereitung V-1 bis V-6: **erstellt** in `spikes/e-002/` (siehe README dort). V-6: Schlüssel liegt bereit; das Kostenlimit ist **technisch eingebaut** (Schutz-Proxy mit Obergrenzen für Anfragen und Tokens, nur ein Modell, kein Streaming); ein Ausgabenlimit in der Anthropic-Konsole ist als zweite Linie empfohlen. Validiert gegen eine Referenzattrappe, nicht gegen einen Kandidaten; K6 ist mit echtem Aufruf geprüft, K3 (manuell) noch nicht.
2. Briefing prüfen lassen, dann drei Agenten starten (`spikes/e-002/RUNBOOK.md`).
3. Messen, Protokolle schreiben, auswerten (Abschnitt 6), Ergebnis als ADR-004.
