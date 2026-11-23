# Wiki-Log

Nur anhängen. Format: `## [YYYY-MM-DD] <ingest|query|lint|promote> | <Quelle>` und darunter ein bis drei Zeilen.

## [2026-11-19] ingest | Aufbau der Struktur
Gerüst von `docs/` und `wiki/` angelegt (Vorschlag, noch nicht gemergt).
## [2026-11-20] ingest | Session: Projektkontext und Gedächtnis-Verbot
Seiten `concepts/projektkontext-chronos-v3.md` und `lessons/wissen-nur-im-wiki.md` angelegt; Konvention in `wiki/README.md` ergänzt.
## [2026-11-20] ingest | Session: arc42 geleert
Auf Wunsch des Nutzers wurde `docs/arc42/` bis auf die `00-kapitelbeschreibung.md` je Kapitel geleert (Neuanfang, Lösungen werden neu betrachtet); alte Inhalte nur in der Git-Historie. Verweise darauf in `docs/README.md`, `docs/req42/` und `wiki/README.md` wurden bereinigt (Einträge entfallen bzw. "noch zu erstellen").
## [2026-11-20] ingest | Session: req42-Neuaufbau, Runde 1-3
Key Learnings und Eckpunkte vom Product Owner erfasst (`concepts/key-learnings-chronos-root.md`); Alt-req42 wird neu geschrieben.
## [2026-11-20] ingest | Session: req42 neu geschrieben
Alt-req42 verworfen, req42 für chronos-v3 komplett neu (Z, SH, SC, F/FA, M, QA, RB, Glossar, BM, TS, RM, RA); Entscheidungen in key-learnings-chronos-root. Freigabe durch Menschen steht aus.
## [2026-11-20] ingest | Session: req42 Runde 5
RB-001 neu, RB-007 entfallen, RB-010/011, F-014..F-018, Z-008, QA-009, RA-010 ergänzt.
## [2026-11-20] ingest | Session: RA-008 Runde 6
Offene Fragen mit dem Product Owner geklärt; Vorschlag `proposals/2026-11-20-ra-008-offene-fragen-runde-6.md` (docs/ unverändert, Freigabe steht aus).
## [2026-11-20] ingest | Session: Runde 6 übernommen, Runde 7
Proposal Runde 6 vom Product Owner freigegeben und in docs/req42 eingearbeitet (Freigabe liegt vor). Neue Ziele Z-009 (Benachrichtigungsbudget, QA-010) und Z-010 (Rückmeldungen automatisch einholen), F-005/F-008/M-004/FA-005/FA-008 ergänzt. RA-008 aktualisiert.
## [2026-11-20] ingest | Session: Runde 8
Leitungsmeldung bei ausbleibender Rückmeldung (2 Tage vorher) und Backup-Ziel (S3-kompatibler EU-Objektspeicher) in docs/req42 übernommen (vom Product Owner in der Session entschieden).
## [2026-11-20] ingest | Session: Runde 9
Mindestbreite 320 px (QA-005) und Antwortquote >= 80 % (Z-001) vom Product Owner entschieden und in docs/req42 übernommen.
## [2026-11-20] ingest | Session: Runde 10
Zeitplan (Meilensteine ohne Termine), Budget (Cluster-Budget, geringe Zusatzkosten) und Vertretung (keine) vom Product Owner entschieden; RM-*, RA-003, RA-008, RA-009 angepasst.
## [2026-11-20] ingest | Session: Runde 11
Kostenobergrenze 10 Euro/Monat mit KI-Pause bei Erreichen vom Product Owner entschieden; RA-009, F-018, RA-008 angepasst.
## [2026-11-20] ingest | Session: arc42 befüllt
Alle zwölf arc42-Kapitel als Entwurf aus req42 abgeleitet, ohne Entscheidungen (Kapitel 9 listet E-000..E-017 offen). Vorschlag `proposals/2026-11-20-sc-001-kontext-ergaenzen.md`; Konzeptseite `concepts/arc42-entwurf-stand.md`.
## [2026-11-20] promote | Proposal SC-001/QA-008
Vorschlag auf Anweisung des Nutzers in docs/req42 übernommen (SC-001: KI-Anbieter, Ferien-API; QA-008: Satz korrigiert).
## [2026-11-20] ingest | Session: E-000 entschieden
ADR-001 (Rangfolge der Qualitätsziele) im Entwurf angelegt; arc42 1.2, 9, 10 angepasst.
## [2026-11-20] ingest | Session: E-001 entschieden
ADR-002 (Monolith plus Worker) im Entwurf; arc42 Kapitel 4, 5, 7, 9 angepasst.
## [2026-11-20] ingest | Session: E-003 entschieden, E-002 Analyse
ADR-003 (PostgreSQL, eigene Instanz) im Entwurf. E-002-sprachwahl-analyse.md mit Pro/Contra und Bibliotheken je Sprache (inkl. Rust); Bibliotheksstand nicht geprüft (▲), Spike vorgeschlagen.
## [2026-11-20] ingest | Session: E-002 Spike-Kriterien
Python und Java/Kotlin ausgeschieden (Product Owner); Vorschlag E-002-spike-kriterien.md (K.-o., Metriken M-1..M-15, Q-1..Q-5, Gewichtung aus ADR-001). Bestätigung steht aus.
## [2026-11-20] ingest | Session: E-002 Spike-Kriterien festgelegt
Offene Fragen beantwortet (Schwellen wie vorgeschlagen, 8 h parallel durch Agenten, amd64, lokales Keycloak, Rank-Order-Centroid, Frontend-Brücke zählt). Abschnitt 2a Vorbereitung V-1..V-6 ergänzt.
## [2026-11-20] ingest | Session: Spike-Vorbereitung V-1, V-2
spikes/e-002/common angelegt: V-1 Aufgabenbeschreibung (HTTP-Verträge), V-2 Abnahmesuite (Python-Standardbibliothek, 65 Tests, Golden-RRULE-Katalog mit dateutil), bridge-check. Ungetestet gegen einen Dienst; Annahmen (Mailpit-API, Keycloak-Formular) in acceptance/README.md. K5-Semantik präzisiert (Idempotenzschlüssel).
## [2026-11-20] ingest | Session: Spike-Vorbereitung V-3..V-6 komplett
V-4 Umgebung (compose, Keycloak-Realm, Mailpit, Mock-Kanal, stack.sh, Push-Testseite), Referenzattrappe (Python/PostgreSQL), V-3 Mess- und Auswertungsskripte, V-5 Briefing/Arbeitsbereiche/Phase 2, V-6 Schlüsselhandhabung und Geheimnisprüfung. Suite gegen die Attrappe validiert (Phase 1 und 2 grün, außer K6/K3). Funde: rootless Docker braucht lesbare Mounts; Keycloak-Secure-Cookies; E-Mail-Header RFC 2047; Attrappe-Rekursionsfehler. Offen: V-6 Schlüssel und Ausgabenlimit (Product Owner).
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 1
Product Owner: ADR-001..003 freigegeben; E-006 Outbox, E-010 S3 austauschbar/Schlüssel beim Betreiber, E-011 generisches SMTP, E-012 Cluster-Bestand, E-013 materialisieren, E-014 vorausberechnen, E-015 occasion. E-007 zurückgestellt (Vorschlag FA-017 offen), E-008 zurückgestellt. Noch offen: E-004, E-005, E-009, E-016, E-017, Detailfragen in K-005/K-007/K-008/K-010, Kapitel 7.
## [2026-11-20] ingest | Session: V-6 und Arbeitsbereiche
Anthropic-Schlüssel vom Product Owner in .env (git-ignoriert) bereitgestellt; Zeile nach ~/.config/chronos-spike/anthropic.env kopiert (Modus 600), .env auf 600 gesetzt. K6 gegen die Attrappe bestanden. Arbeitsbereiche typescript/go/rust unter ~/spikes/e-002 angelegt. Offen: Ausgabenlimit in der Konsole bestätigen, K3 manuell, Start der Agenten.
## [2026-11-20] ingest | Session: V-6 Kostenlimit technisch
KI-Schutz-Proxy (common/env/ai-guard) eingebaut: hält den echten Schlüssel, erzwingt Obergrenzen (150 Anfragen, 600k/60k Tokens, ein Modell, kein Streaming, max_tokens 1024). Anwendungen sehen den Schlüssel nie. Mit Fake-Upstream getestet, K6 über den Proxy bestanden. Arbeitsbereiche neu erzeugt.
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 2
Product Owner: K-005 Preise aus Anbieterantwort; K-007 UTC plus Terminzone; K-008 Backups im Zyklus, Offenlegung in Datenschutzerklärung; K-010 Termin je Team duplizieren; E-017 eigenes Import-Werkzeug über Operationsschicht; Kapitel 7: zwei Images, je Umgebung eigene PostgreSQL-Instanz. Noch offen: E-009, E-016, K-010 (Rolle→Label, Einstellungen), E-017 Probelauf, Rest Kap. 7, K-007 Übersetzungsformat, K-008 KI-Datenschutz, K-005 Rundung.
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 3
Product Owner: K-010 Rollen und Einstellungen verwerfen; E-017 Probelauf in staging mit echten Altdaten; K-006 KI-Daten unverändert, Offenlegung. Vorschlag zu M-005 angelegt. E-009 und E-016 hängen von E-005/E-002 ab und sind zurückgestellt.
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 4
Product Owner: K-005 nur EUR ganzzahlig; K-007 Übersetzungen als Dateien im Repo; Kap. 7 staging eigene Testdaten (Altdaten nur im Migrationsprobelauf), Deployment per Manifeste/kustomize via CI.
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 5
Product Owner: Importmodus markiert Ereignisse als importiert und stellt nicht zu; K-005 Pauschaltarife für Anbieter ohne Preisangabe; K-007 Plural/Datum nach E-002. E-004, E-005, E-008, E-009, E-016 bewusst bis nach E-002 zurückgestellt (PO-Entscheidung); E-007 wartet auf Annahme des Vorschlags FA-017.
## [2026-11-20] ingest | Session: Agenten in Vagrant-VM
Vagrant-VM (VirtualBox, Ubuntu 24.04, 12 GB/8 CPU) unter spikes/e-002/vm gebaut: kein geteilter Ordner, Benutzer agent ohne sudo, Netzsperre für Host und Heimnetz, Docker/Node/Go/Rust/Claude Code, Arbeitsbereiche und K6-Schlüssel hineinkopiert. Modell claude-opus-5-5; Anmeldung von Claude Code durch den Product Owner in der VM. Erste Netzsperre brach SSH (Antwortpakete an Gateway blockiert) und wurde korrigiert.
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 6
Product Owner: Vorschläge Glossar (occasion), M-005, FA-017 (Soft-Delete) angenommen und in docs/req42 übernommen; E-007 damit erledigt. Kap. 7: prod und staging je 1 vCPU/1 GiB. K-005 kein Rechnungsabgleich. Neuer Vorschlag RB-003. Folgearbeit: weitere Rückgängig-Verweise in req42/arc42, K-004 überarbeiten.
## [2026-11-20] ingest | Session: Agenten gestartet
Product Owner meldete Claude Code in der VM an; Wächter startete um 16:27:52 UTC drei Agenten (claude-opus-5-5, je 8 h Zeitbox, tmux spike-typescript/go/rust). Phase 2 und Abnahme stehen aus (spikes/e-002/vm/README.md, RUNBOOK.md).
## [2026-11-20] ingest | Session: offene arc42-Fragen Runde 7
Product Owner: RB-003 (Budget je Umgebung) angenommen und umgesetzt (RB-003, QA-001); Ressourcenaufteilung je Umgebung wartet auf E-002. Folgeänderungen zu FA-017 als Block-Vorschlag angelegt, Freigabe offen.
## [2026-11-20] ingest | Session: Rückgängig-Folgeänderungen umgesetzt
Block-Vorschlag vom Product Owner freigegeben; req42 (FA-001, FA-014, FA-015, F-001, SC-002, RA-004, RA-010, RM-001, M-004) und arc42 (K-002, K-004, K-006, Kap. 1.2, 4, 6 L-6, 11, 12, ADR-001/002) angepasst.
## [2026-11-23] ingest | Session: E-002 Spikes abgeschlossen, ADR-004 Entwurf
Abnahme und Messung aller drei Spikes in der VM; Product Owner bewertete Q-1 bis Q-5 und K3 (alle bestanden). Rust vorn (90,8 gegen 87,0 und 86,1), Entscheidungsregel nicht erfüllt. Experimente E-002a (jiff statt rrule: Eigenbau 12,5 %) und E-002b (web-push-native, läuft). Entwurf docs/arc42/09-entscheidungen/ADR-004-sprache-und-laufzeit.md mit Liste der abhängigen Entscheidungen (E-004, E-005, E-008, E-009, E-016, ADR-003-Migrationswerkzeug, K-007). Wiki: concepts/e-002-spike-ergebnisse.md.
## [2026-11-23] query | Folgeentscheidungen von E-002 unter Rust
Zusammenstellung der offenen Entscheidungen, die an ADR-004 hängen (E-004, E-005, E-008, E-009, E-016, Migrationswerkzeug, K-007), plus zwei neue aus Rust (Zeitbibliothek, Build/Lieferkette), je mit Optionen, Vor-/Nachteilen und unverbindlichem Vorschlag. Geprüft gegen Rust-Spike-Code und Claude-Doku (weiterhin kein offizielles Rust-SDK; neue API-Version 2026-10-21, Spike sendet 2023-06-01). Wiki: concepts/e-002-folgeentscheidungen-rust.md. docs/ unverändert.
## [2026-11-23] query | E-005 Entscheidungsgrundlage
Auf Wunsch des Nutzers Entwurf docs/arc42/09-entscheidungen/E-005-operationsschicht-analyse.md angelegt (neue Datei, Freigabe offen; Kapitel 9 nicht verlinkt). Befund aus dem Rust-Spike: Berechtigung in jeder Operation (require_member, 19 Stellen), Verlauf/Ereignis von Hand (commit_change), Bündel-ID je Eintrag, Vorschau bei 4 von 10 schreibenden Operationen, Freigabe nur im Client. Vorschlag V2: Rahmen trägt Querschnitt, Vorschau per Probelauf, Freigabe-Beleg im Server, Stapel atomar, RPC.
## [2026-11-23] ingest | Session: Python-Spike und Experimente
Python-Spike (FastAPI/Pydantic/SQLAlchemy/psycopg) gebaut, abgenommen und gemessen; Code-Prüfung mit drei Befunden; Python-Spalte in der Ergebnisseite; E-002a (jiff statt rrule) und E-002b (web-push-native) abgeschlossen. ADR-004 (Entwurf) um Python, E-002a und E-002b ergänzt. Python steht vorläufig bei höchstens 79 Punkten, Rust weiter vorn.
## [2026-11-23] ingest | Session: E-002 entschieden, ADR-004 freigegeben
Product Owner entschied E-002 (Rust, rrule behalten und isolieren, web-push-native nach bestandenem K3, Pipeline-Prüfung der Sicherheitsmeldungen, Python ausgeschieden, kein Opus-Wiederholungslauf) und gab ADR-004 frei. K3 für web-push-native in Firefox und Chrome bestanden. Offen: Differenztest RRULE (Umsetzung), VAPID-Schlüssel-Endpunkt in FA ergänzen (E-004), nächste Entscheidung E-005.
## [2026-11-23] ingest | Session: E-005 entschieden, ADR-005
Product Owner entschied E-005 als Gesamtvariante V2 (Rahmen trägt Querschnitt, Vorschau per Probelauf, Freigabe-Beleg im Server, Stapel atomar, RPC). Neu: docs/arc42/09-entscheidungen/ADR-005-operationsschicht.md (freigegeben); Kapitel 9 (Stand, Zeile E-005), K-006 (Offen → Entschieden) und E-005-Analyse nachgezogen. Offen: Spike-Erweiterung E-005a (schemars statt utoipa, Probelauf unter Last), Stapel-Obergrenze, Beleg-Ablauf, Sprache der Operationsbeschreibungen, Folgeänderungen K-002, K-004, Kap. 5, Kap. 11 R-A2. E-009 jetzt entscheidbar.
## [2026-11-23] query | E-009 Entscheidungsgrundlage
Analyse docs/arc42/09-entscheidungen/E-009-ki-anbindung-analyse.md (Entwurf) mit T1 bis T8 und Varianten V1 bis V3; Vorschlag V2 (eigener Client hinter AiProvider, Schleife im Server, Gespräch 24 h, Limit vorab + Deckel + Caching, Start Haiku 5.5 mit Prüfkatalog, Anthropic direkt). Claude-Doku 2026-11-23: kein EU-`inference_geo` (nur global/us), Preise Haiku/Sonnet/Opus 5.5, API-Version 2026-10-21 ohne temperature. Antwort enthält keinen Preis → Tarif im System (K-005). Spike-Befund: ai.ask als Operation mit Adapter widerspricht ADR-005, Assistent wird eigener Baustein.
## [2026-11-23] query | E-009: LiteLLM-Gateway
Product Owner möchte Modell und Anbieter zur Laufzeit wechseln und hat bereits einen LiteLLM-Proxy. Analyse um T1-E und Variante V2-G ergänzt. LiteLLM-Doku 2026-11-23: Kosten im Kopf x-litellm-response-cost (nur ohne Streaming aufgeschlüsselt), Alias änderbar ohne Neustart nur mit STORE_MODEL_IN_DB, Inhalte standardmäßig nicht gespeichert, Budgets je virtuellem Schlüssel, tatsächliches Modell über x-litellm-model-id (Feld model im Body unzuverlässig), Caching unter Mindestlänge still ausgelassen, Werkzeug-Übersetzung auf Nicht-Anthropic-Modelle nicht belegt.
## [2026-11-23] query | E-009: Europäische KI-Anbieter
Preise und Bedingungen von Mistral (Small 4 0,15/0,60 USD, Large 4 0,70/2,10 USD, EU-Endpunkt +10 %, Caching 10 %, ZDR auf Antrag), IONOS (nur DE, keine Speicherung, kein Training, offene Modelle, z. B. gpt-oss-120b 0,15/0,65 EUR netto, LiteLLM nur über custom_openai) und STACKIT (Preise, sonst kaum belegbar) in die E-009-Analyse übernommen, mit Kosten je Aufgabe. Scaleway und OVHcloud blockieren automatische Abrufe (403 bzw. Weiterleitungsschleife); nur LiteLLM-Unterstützung belegt. Wiederholung lohnt nicht ohne Browser.
## [2026-11-23] ingest | Session: E-009 entschieden, ADR-006
Product Owner entschied V2-G (LiteLLM-Gateway) und nur Anbieter mit garantiertem EU-Datenstandort. Neu: docs/arc42/09-entscheidungen/ADR-006-ki-anbindung.md (freigegeben). Nachgezogen: Kapitel 9, K-006, Kapitel 3.1/3.2 (Gateway als Nachbar), Veränderlichkeit, Kapitel 5 (Assistent im Web-Prozess), E-009-Analyse. Widerspruch zu req42 (F-015, SC-001 „Start mit Claude“) als Vorschlag proposals/2026-11-23-ki-anbieter-eu.md. Offen: Prüfkatalog, Standardmodell, KI-Anteil am Budget, Kapitel 11 (neue Risiken Gateway-Fehlkonfiguration, Modellqualität), Ort/Version des Gateways.
## [2026-11-23] promote | Vorschlag KI-Anbieter nur EU angenommen
Product Owner nahm proposals/2026-11-23-ki-anbieter-eu.md an; F-015 (Entscheidung, Offen) und SC-001 (Diagramm, Zeile KI-Anbieter, neue Zeile KI-Gateway) angepasst. RA-008 bleibt als Protokoll unverändert.
