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
