---
title: Offene Architekturentscheidungen
status: entwurf
quellen: [req42, arc42 Kapitel 3 bis 8]
---

# Kapitel 9: Architekturentscheidungen

**Stand: sechs Entscheidungen angenommen ([ADR-001](ADR-001-prioritaet-der-qualitaetsziele.md) Priorisierung der Qualitätsziele, [ADR-002](ADR-002-zerlegung-monolith-plus-worker.md) Zerlegung, [ADR-003](ADR-003-datenbank-postgresql.md) Datenbank, jeweils freigegeben vom Product Owner am 2026-11-20, sowie [ADR-004](ADR-004-sprache-und-laufzeit.md) Sprache und Laufzeit und [ADR-005](ADR-005-operationsschicht.md) Operationsschicht und [ADR-006](ADR-006-ki-anbindung.md) KI-Anbindung, freigegeben am 2026-11-23); weitere Entscheidungen aus dem Gespräch vom selben Tag stehen in der Tabelle.** Diese Liste sammelt, was zu entscheiden ist, warum, und was die Entscheidung bindet. Jede getroffene Entscheidung wird als eigene Datei `ADR-nnn-<titel>.md` nach [Vorlage](_vorlage-adr.md) angelegt und hier verlinkt. Ersetzte Entscheidungen werden nicht überschrieben, sondern mit `status: ersetzt` markiert ([docs/README](../../README.md)).

Gemeinsame Bewertungsgrößen aller Entscheidungen: Qualitätsziele ([1.2](../01-einfuehrung/02-qualitaetsziele.md)), Budget ([RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md)), Ein-Personen-Team mit Agenten, Migrationstauglichkeit.

## Was durch req42 bereits **vorgegeben** ist (keine ADR nötig)

k3s als Plattform, Keycloak als Identitätsdienst, S3-kompatibler EU-Objektspeicher für Backup, SMTP-Relay/EU-Anbieter für Mail, Web Push als Kanal, RFC 5545 für Serien und Feed, Operationsschicht für UI und Assistent, Kosten je Benutzer/Team. Siehe [Kapitel 2](../02-randbedingungen/01-randbedingungen.md).

## Zu entscheiden

Die Spalte „Vorab“ nennt, was zuerst geklärt sein muss. Optionen sind Anstöße, keine vollständige Liste und keine Empfehlung.

| ID | Frage | Treiber | Optionen (Beispiele) | Vorab | Status |
|---|---|---|---|---|---|
| E-000 | Priorisierung der Qualitätsziele | alle Abwägungen | Reihenfolge der fünf Ziele durch den Product Owner | – | **entschieden**: [ADR-001](ADR-001-prioritaet-der-qualitaetsziele.md) |
| E-001 | Zerlegung und Deployment-Einheiten | QA-001, QA-003, Team-Größe | modularer Monolith, wenige Dienste, getrennte Hintergrundverarbeitung | E-000 | **entschieden**: [ADR-002](ADR-002-zerlegung-monolith-plus-worker.md) |
| E-002 | Programmiersprache, Laufzeit, Framework | RB-003 (JVM zu begründen), Agentenfähigkeit, Pflegbarkeit | JVM-Stack, Go, Node/TypeScript, Python, Rust | E-001 | **entschieden (PO 2026-11-23)**: Rust (axum, sqlx, serde, utoipa); `rrule` behalten und isolieren, `web-push-native` (K3 bestanden), Pipeline-Prüfung der Sicherheitsmeldungen; Python bestätigt ausgeschieden. [Analyse](E-002-sprachwahl-analyse.md), [Spike-Kriterien](E-002-spike-kriterien.md), [ADR-004](ADR-004-sprache-und-laufzeit.md), freigegeben vom Product Owner am 2026-11-23 |
| E-003 | Datenbank | Budget, Migration, Team-Baum, Verlauf, Backup | relational (PostgreSQL, SQLite), Dokument-DB | E-001 | **entschieden**: [ADR-003](ADR-003-datenbank-postgresql.md) |
| E-004 | Frontend-Ansatz | mobil zuerst, Web Push, einfache UI, i18n | serverseitig gerendert, SPA, PWA | E-002 | offen |
| E-005 | Form der Operationsschicht und ihrer maschinenlesbaren Beschreibung | RB-011, QA-003 c, FA-015 | eine Operationsdefinition erzeugt API-Endpunkte und Assistent-Werkzeuge; getrennte Beschreibungen | E-001, E-002 | **entschieden (PO 2026-11-23)**: Variante V2, Rahmen trägt den Querschnitt (Berechtigung, Transaktion, Verlauf, Ereignis), Vorschau per Probelauf, Freigabe-Beleg im Server, Stapel atomar, RPC. [Analyse](E-005-operationsschicht-analyse.md), [ADR-005](ADR-005-operationsschicht.md); offen: Spike-Erweiterung E-005a (u. a. `schemars` statt utoipa) |
| E-006 | Ereignis-, Zustell- und Zeitsteuerungsmechanismus (Web hält fest, Worker arbeitet ab; Pflicht aus ADR-002) | QA-002, QA-004, QA-010, Budget | Ereignisse in der Datenbank festhalten und abarbeiten, externe Warteschlange, Scheduler im Prozess | E-001, E-003 | **entschieden (PO 2026-11-20)**: Ereignisse in der Datenbank festhalten und abarbeiten (Outbox-Tabelle) |
| E-007 | Mechanismus für Verlauf und Rückgängig | FA-017, alle Fachfunktionen | Vorher-Zustand speichern, Differenzen, Ereignisprotokoll als Quelle | E-003 | **durch Anforderung erledigt (PO 2026-11-20)**: FA-017 auf Soft-Delete reduziert, kein allgemeiner Rückgängig-Mechanismus; K-004 ist entsprechend zu überarbeiten (Verlauf als Anzeige, Wiederherstellung gelöschter Objekte) |
| E-008 | Einbindung Keycloak, Sitzung und Gast-Identität | RB-002, Z-004, QA-007 | Standardprotokoll des Dienstes, Sitzung in Chronos oder Token im Browser; Gast als eigene Person | E-004 | zurückgestellt bis E-002 und E-004 (PO 2026-11-20) |
| E-009 | KI-Anbindung, Anbieterneutralität, Limit | FA-015, RB-010, RA-010 | eigene schmale Anbieterschnittstelle, Bibliothek | E-005 | **entschieden (PO 2026-11-23)**: Variante V2-G, KI-Gateway (LiteLLM) mit festem Modellnamen, Assistent als Baustein im Web-Prozess mit Schleife im Server, Gespräch 24 h, Kosten aus dem Gateway; nur Anbieter mit garantiertem EU-Datenstandort. [Analyse](E-009-ki-anbindung-analyse.md), [ADR-006](ADR-006-ki-anbindung.md); offen: Prüfkatalog und Standardmodell, KI-Anteil am Budget, Anpassung F-015/SC-001 (Vorschlag im Wiki) |
| E-010 | Backup-Anbieter und Schlüsselverwaltung | QA-006, QA-007, 10 €-Limit | Anbieter nach Preis und Standort; Schlüssel beim Betreiber | – | **entschieden (PO 2026-11-20)**: S3-Schnittstelle, Anbieter austauschbar nach Preis/EU-Standort, clientseitige Verschlüsselung, Schlüssel beim Betreiber |
| E-011 | Mailversand-Anbieter | BM-001, RB-010 | SMTP-Relay, EU-Anbieter | – | **entschieden (PO 2026-11-20)**: generisches SMTP, EU-Anbieter per Konfiguration austauschbar |
| E-012 | Beobachtungswerkzeuge im Budget | QA-001, QA-002 | Cluster-Bestand nutzen, leichtgewichtige Metriken | E-001 | **entschieden (PO 2026-11-20)**: Bestand im Cluster nutzen |
| E-013 | Serien: Vorkommen speichern oder berechnen | FA-014, Rückmeldung je Vorkommen, Feed | materialisieren (Horizont), virtuell mit Ausnahmen | E-003 | **entschieden (PO 2026-11-20)**: Vorkommen materialisieren (Horizont) |
| E-014 | Erinnerungsplanung und Bündelung | QA-010, Z-010 | beim Planen vorausberechnen, bei Fälligkeit berechnen | E-006 | **entschieden (PO 2026-11-20)**: beim Planen vorausberechnen |
| E-015 | Namenskonflikt `event` (Veranstaltung, Ereignis) | Glossar | z. B. Veranstaltung `gathering`, Ereignis `event` | – | **entschieden (PO 2026-11-20)**: Veranstaltung = `occasion`, Ereignis bleibt `event`; Glossar-Änderung siehe wiki/proposals/2026-11-20-glossar-occasion.md |
| E-016 | Teststrategie und Architekturtests | QA-003, RB-007 entfallen | Abhängigkeitsregeln, Szenariotests aus Kapitel 6 | E-002 | offen |
| E-017 | Durchführung der Datenübernahme | FA-012, RA-005 | Werkzeug, Probelauf in staging, Umgang mit Ereignissen beim Import | E-003 | **teilweise entschieden (PO 2026-11-20)**: eigenes Import-Werkzeug über die Operationsschicht; Probelauf in staging mit echten Altdaten (PO 2026-11-20); Importmodus: Ereignisse werden erzeugt, als „importiert“ markiert und nicht zugestellt (PO 2026-11-20) |

## Empfohlene Reihenfolge

E-000 → E-001 → E-002 / E-003 → E-005 / E-006 / E-007 → übrige. Die ersten vier bestimmen fast alles andere; sie sollten **gemeinsam** mit dem Product Owner entschieden werden, bevor Kapitel 5 (Ebene 2) und Kapitel 7 (Zuordnung) ausgebaut werden.
