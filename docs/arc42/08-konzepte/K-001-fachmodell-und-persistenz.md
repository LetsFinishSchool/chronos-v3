---
title: K-001 Fachmodell und Persistenz
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 M-001, M-003, M-005, FA-017, RB-004]
---

# K-001: Fachmodell und Persistenz

**Vorgaben:** Das Fachmodell ist [M-001](../../req42/05-modelle/M-001-fachdatenmodell.md), die Zustandsautomaten sind [M-003](../../req42/05-modelle/M-003-zustaende.md).

- **Person** ist entweder Konto-Person (Keycloak-Kennung) oder Gast-Person (Name, ohne Konto). Beide antworten gleichwertig ([FA-005](../../req42/04-product-backlog/anforderungen/FA-005-rueckmeldung.md)); ein Gast kann sein Handeln in ein Konto übernehmen (Runde 6).
- **Team-Baum** beliebiger Tiefe, zyklenfrei. Abfragen „alle Teams/Mitglieder oberhalb/unterhalb“ sind Kernoperationen.
- **Termin** gehört genau einem Team, höchstens einer Veranstaltung; Art (Treffen | Frist/Marke); Status geplant, abgesagt, gelöscht, vergangen. Rückmeldung gilt je Termin bzw. Vorkommen.
- **Gelöscht** heißt 30 Tage wiederherstellbar samt Unter-Teams, Mitgliedschaften, Rückmeldungen, Labels und Nachrichten ([FA-017](../../req42/04-product-backlog/anforderungen/FA-017-rueckgaengig-machen.md)). Das Modell muss „gelöscht, aber wiederherstellbar“ als eigenen Zustand kennen und danach endgültig entfernen.
- **Zeit:** Beginn/Ende in der Zeitzone des Termins (Standard: Team, Europe/Berlin); Anzeige in der Zeitzone der Person ([K-007](K-007-mehrsprachigkeit-und-zeitzonen.md)).
- **Datensparsamkeit:** nur nötige personenbezogene Daten; keine Daten von Kindern und Eltern ([K-008](K-008-sicherheit-und-datenschutz.md)).
- **Migrationstauglichkeit:** Jede Modellentscheidung ist gegen [M-005](../../req42/05-modelle/M-005-migrationsabbildung.md) zu prüfen. Offene Abbildungen (Termin-Besitz je Team, Rolle → Label) hängen am Altschema ([RA-005](../../req42/12-risiken-annahmen/RA-005-migration-altmodell-passt-nicht.md)).

**Datenbank:** PostgreSQL ([ADR-003](../09-entscheidungen/ADR-003-datenbank-postgresql.md), Entwurf). **Offen:** Serien: Vorkommen gespeichert oder berechnet (E-013), Benennung `event` ([E-015](../09-entscheidungen/01-offene-entscheidungen.md)).
