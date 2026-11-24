---
id: M-001
title: Fachdatenmodell
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: modell
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-001, F-003, F-004, F-005, F-007]
---

# M-001: Fachdatenmodell

```mermaid
erDiagram
  PERSON ||--o{ MITGLIEDSCHAFT : hat
  TEAM ||--o{ MITGLIEDSCHAFT : umfasst
  TEAM ||--o{ TEAM : enthaelt_unterteams
  TEAM ||--o{ TERMIN : plant
  TEAM ||--o{ VERANSTALTUNG : richtet_aus
  VERANSTALTUNG ||--o{ TERMIN : buendelt
  TERMIN ||--o{ RUECKMELDUNG : sammelt
  SERIE ||--o{ TERMIN : erzeugt_vorkommen
  SERIE ||--o{ AUSNAHME : hat
  TEAM ||--o{ ZEITRAUMSREGEL : legt_fest
  TEAM ||--o{ FERIENZEITRAUM : hinterlegt
  PERSON ||--o{ KOSTENPOSTEN : verursacht
  TERMINFINDUNG ||--o{ VORSCHLAG : enthaelt
  VORSCHLAG ||--o{ STIMME : erhaelt
  TERMIN ||--o{ NACHRICHT : enthaelt
  PERSON ||--o{ LABELZUWEISUNG : traegt
  LABEL ||--o{ LABELZUWEISUNG : vergeben
  EINLADUNGSLINK }o--|| TEAM : fuer
  PERSON ||--o{ BENACHRICHTIGUNG : empfaengt
  PERSON ||--o{ KANAL : konfiguriert
  PERSON ||--o{ AENDERUNGSVERLAUF : verursacht
```

| Begriff | Eigenschaften |
|---|---|
| Person | Konto-Person (Keycloak-Kennung) **oder** Gast-Person (Name, aus Einladungslink, ohne Konto) |
| Team | Name, optional übergeordnetes Team (Baum, beliebige Tiefe) |
| Mitgliedschaft | Person in Team; alle Mitglieder gleichberechtigt; Mitgliedschaft erbt nach oben ([M-002](M-002-berechtigungen.md)) |
| Veranstaltung | Titel, Beschreibung, Zeitraum; gehört einem Team |
| Termin | Team, optional Veranstaltung, Art (Treffen \| Frist/Marke), Titel, Ort, Beginn, Ende, Status ([M-003](M-003-zustaende.md)) |
| Rückmeldung | Person zu Termin: offen \| zugesagt \| abgesagt \| zeitweise, ggf. Hinweis |
| Terminfindung / Vorschlag / Stimme | Vorschläge mit Zeitraum, Stimmen je Person |
| Label / Labelzuweisung | Freitext; Person trägt Label für genau einen Bereich (Team, Veranstaltung oder Termin) |
| Einladungslink | Token, Ziel (Team, Termin, Terminfindung), Widerruf, Ablauf (Gastlink: Terminende + 30 Tage) |
| Nachricht | Text, Autor, Zeitpunkt, System- oder Nutzernachricht |
| Kanal / Einstellung | Kanal je Person (Web Push, E-Mail, optional Messenger) und Einstellungen je Ereignisart |
| Serie | RRULE (RFC 5545), Beginn, Team, Ausnahmen (einzelne Vorkommen, Ferienzeiträume); Vorkommen sind Termine mit Rückmeldung je Vorkommen |
| Ferienzeitraum | Team, Name, Von, Bis; Ausnahme für Serien |
| Zeitraumsregel | Team, Zeitraum, Aktion (absagen); wirkt auf bestehende und später angelegte Termine ([F-016](https://github.com/LetsFinishSchool/chronos-v3/issues/88)) |
| Kostenposten | Benutzer oder Team, Auslöser, Anbieter, Zeitpunkt, Menge, Betrag ([RB-010](../07-randbedingungen/RB-010-kostenzuordnung.md)) |
| Änderungsverlauf | Akteur (Person oder Assistent im Auftrag einer Person), Aktion, Vorher-Zustand zur Wiederherstellung, Zeitpunkt, Bündel-ID; für Teams, Mitgliedschaften, Termine, Veranstaltungen |
| Benachrichtigung | Ereignis, **Auslöser**, Empfänger, Kanal, Ergebnis, Zeitpunkt ([QA-002](../06-qualitaet/QA-002-nachvollziehbarkeit.md)) |

Begriffe: [Glossar](../08-terminologie/glossar.md). Migration: [M-005](M-005-migrationsabbildung.md).
