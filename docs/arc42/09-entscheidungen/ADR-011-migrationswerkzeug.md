---
id: ADR-011
title: Migrationswerkzeug: sqlx-Migrationen als Job vor dem Rollout
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-019]
quellen: [ADR-002, ADR-003, ADR-004, ADR-009, RB-005, QA-007, ticket-typen.md (DoD: Migrationen nur vorwärts), Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-011: Migrationswerkzeug: sqlx-Migrationen als Job vor dem Rollout

**Hinweis:** Der Product Owner hat die Entscheidung am 2026-11-24 im Gespräch getroffen. Dieser Text wurde vom Product Owner am 2026-11-24 freigegeben. Er füllt die Aussage „Werkzeug folgt aus E-002“ in [ADR-003](ADR-003-datenbank-postgresql.md). Die neue Nummer E-019 ist in Kapitel 9 ergänzt.

## Kontext
Schemaänderungen laufen über versionierte Migrationen ([ADR-003](ADR-003-datenbank-postgresql.md)); die Definition of Done lässt Migrationen **nur vorwärts** zu, der Rückweg ist ein Backup. Web und Worker sind zwei Deployments aus demselben Image ([ADR-002](ADR-002-zerlegung-monolith-plus-worker.md)), der Cluster ist ein geteiltes k3s mit Helm ([RB-005](../../req42/07-randbedingungen/RB-005-betrieb-auf-geteiltem-k3s-cluster.md)). `sqlx::query!` prüft SQL beim Übersetzen und braucht das Schema. Das Importwerkzeug (E-017) nutzt dieselben Migrationen.

## Optionen
1. `sqlx::migrate!` eingebettet, läuft beim Start von Web und Worker.
2. **`sqlx::migrate!` eingebettet, aber nur über den Unterbefehl `chronos migrate` als Job vor dem Rollout; Web und Worker prüfen beim Start nur die Schemaversion.**
3. `refinery`.
4. Sprachneutrales Werkzeug (Flyway, Atlas, dbmate) als eigener Job.

Vor- und Nachteile der abgelehnten Optionen:

| Option | Vorteile | Nachteile |
|---|---|---|
| 3 `refinery` | Auch Migrationen in Rust-Code | Zusätzliche Abhängigkeit ohne klaren Mehrwert gegenüber `sqlx::migrate!` |
| 4 Sprachneutrales Werkzeug (Flyway, Atlas, dbmate) als eigener Job | Übersteht einen Sprachwechsel; Atlas kann Schemadiffs | Zweites Werkzeug und Image; `sqlx::query!` braucht trotzdem das Schema |


## Entscheidung (PO, 2026-11-24)
**Option 2.**
1. Migrationen sind SQL-Dateien im Repository, eingebettet über `sqlx::migrate!` (Prüfsummen, Advisory-Lock).
2. Das Binary hat einen Unterbefehl `chronos migrate`. Er läuft als **Job vor dem Rollout** (Helm-Hook oder Init-Container; Ausgestaltung beim Helm-Chart festlegen, Reihenfolge testen).
3. Web und Worker führen **keine** Migrationen aus. Sie prüfen beim Start die Schemaversion und warten oder brechen ab, wenn sie nicht passt.
4. Ein fehlgeschlagener Job blockiert das Rollout; die alte Version läuft weiter.
5. Migrationen nur vorwärts (DoD); vor jedem Produktionsrollout ein Backup als Rückweg.
6. Migrationen sind so zu schreiben, dass alte und neue Version kurz nebeneinander laufen (erst erweitern, dann umstellen, dann aufräumen).
7. Das Importwerkzeug (E-017) ist ein weiterer Unterbefehl desselben Binarys und nutzt dieselben Migrationen. Für lokale Entwicklung und Tests kann `chronos migrate` beim Start per Schalter laufen.
8. Getrennte Datenbankbenutzer (Migrationsbenutzer mit DDL-Rechten, Anwendungsbenutzer ohne).

## Folgen
**Leichter:** Ein Fehler in der Migration bricht das Rollout ab statt den Pod abstürzen zu lassen; ein Werkzeug, ein Image; Tests (`#[sqlx::test]`), Import und Betrieb nutzen dieselben Dateien.

**Schwerer:** Ein Job und Helm-Konfiguration mehr; Schemaversionsprüfung in Web und Worker; Disziplin bei Migrationen, die alte und neue Version vertragen müssen; kein automatischer Rückweg (Backup).

**Bindet:** [ADR-009](ADR-009-teststrategie-und-architekturregeln.md) (Datenbanktests nutzen dieselben Migrationen); Helm-Chart und CI (Reihenfolge Job vor Rollout); E-017 (Import als Unterbefehl).

## Festgelegte Werte (PO, 2026-11-24)
- **Getrennte Datenbankbenutzer** (Punkt 8 ist entschieden): Migrationsbenutzer mit DDL-Rechten, Anwendungsbenutzer ohne.
- **Form des Jobs:** Helm-Hook (`pre-install`/`pre-upgrade`) als Job, einmal je Release; das Secret des Migrationsbenutzers muss vor dem Hook existieren.

## Wann überprüfen?
- Mehrere Dienste oder Sprachen teilen sich die Datenbank (dann sprachneutrales Werkzeug).
- Migrationen werden so umfangreich oder gefährlich, dass Schemadiffs und Prüfung gefährlicher Änderungen nötig werden (dann Atlas).
- Der Job vor dem Rollout lässt sich im Cluster nicht zuverlässig einrichten (dann Option 1).
