---
id: ADR-003
title: Datenbank: PostgreSQL in eigener Instanz
status: angenommen
freigegeben-am: 2026-11-20
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-003]
quellen: [Gespräch mit dem Product Owner 2026-11-20, ADR-001, ADR-002, Gespräch mit dem Product Owner 2026-11-25 (Version)]
---

# ADR-003: Datenbank: PostgreSQL in eigener Instanz

## Kontext
Zwei Prozesse (Web, Worker) greifen auf dieselbe Datenbank zu ([ADR-002](ADR-002-zerlegung-monolith-plus-worker.md)). Gebraucht werden: Team-Baum beliebiger Tiefe, Transaktionen über Zustand, Verlauf und Ereignis, ein Auftragsmechanismus für den Worker ([E-006](01-offene-entscheidungen.md)), verschlüsseltes tägliches Backup in S3 (RPO 24 h). Budget insgesamt rund 1 GiB ([RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md)). Im Cluster gibt es **keine** geteilte PostgreSQL-Instanz, die Chronos nutzen könnte.

## Optionen
PostgreSQL; SQLite (beide Prozesse auf derselben Node mit gemeinsamem Volume, ein Schreiber); Dokumentendatenbank (passt schlecht zu Baum, Transaktionen, Verlauf).

## Entscheidung
**PostgreSQL**, als **eigene Instanz für Chronos** im Cluster. Gründe: Zwei Prozesse und gleichzeitiger Zugriff sind unproblematisch; Rekursion für den Team-Baum; Auftragsabarbeitung ohne Zusatzdienst möglich; Standardverfahren für Backup und Wiederherstellung; Änderbarkeit (ADR-001 Platz 1) wird nicht durch Plattformbindung (gemeinsames Volume auf einer Node) eingeschränkt.

## Folgen
- Die Datenbank zählt zum Chronos-Budget (Annahme aus [QA-001](../../req42/06-qualitaet/QA-001-ressourceneffizienz.md), jetzt zwingend, da es keine geteilte Instanz gibt). Sie ist für niedrigen Speicherbedarf zu konfigurieren; die tatsächliche Größe ist per Messung zu belegen.
- Betrieb der Datenbank (Updates, Backup, Wiederherstellungstest) liegt beim Betreiber ([RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)).
- Backup: Abzug, clientseitig verschlüsselt, nach S3 (Anbieter und Schlüssel: E-010).
- E-006 darf die Datenbank als Grundlage für Ereignisse und Aufträge nutzen.
- **Version: PostgreSQL 19**, die aktuelle Hauptversion (PO 2026-11-25). Entwicklung, CI und Cluster nutzen dieselbe Hauptversion; ein Wechsel der Hauptversion ist ein eigener Schritt mit Backup und Wiederherstellungstest.
- Zuschnitt prod/staging: je Umgebung eine eigene Instanz (PO 2026-11-20, Kapitel 7).
- Schemaänderungen laufen über versionierte Migrationen (Werkzeug: sqlx-Migrationen als Job vor dem Rollout, siehe [ADR-011](ADR-011-migrationswerkzeug.md), Entwurf).

## Wann überprüfen?
Wenn die gemessene Datenbank allein das Budget sprengt, oder wenn eine geteilte Instanz im Cluster verfügbar wird.
