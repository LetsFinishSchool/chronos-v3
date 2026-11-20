---
title: Entscheidungen zu RA-008 (Runde 6)
datum: 2026-11-20
betrifft: docs/req42/12-risiken-annahmen/RA-008-offene-fragen.md
art: änderung
status: angenommen
---

## Beobachtung
RA-008 listet offene Fragen. Der Product Owner hat sie in einer Session am 2026-11-20 beantwortet (Quelle: Session, AskUserQuestion).

## Vorschlag
Die folgenden Punkte aus „Noch offen“ nach „Entschieden“ verschieben und in den betroffenen F/QA/RB-Dateien nachziehen.

| Bereich | Entscheidung | Auswirkung |
|---|---|---|
| Team löschen | Kaskade (Unter-Teams, Termine), über „Rückgängig“ wiederherstellbar | Soft-Delete, Bereinigungsjob |
| Zeitzone | Je Team/Termin eine Zeitzone (Default Europe/Berlin), Anzeige umgerechnet; Serien bleiben auf Wanduhrzeit | Zeitzonenfeld am Termin, RRULE mit TZID |
| Aufbewahrung gelöschter Objekte | 30 Tage | Löschjob, DSGVO-konform |
| Antwortskala Terminfindung | Ja / Vielleicht / Nein | Auswertung mit Gewichtung |
| Korrektur versandter Benachrichtigungen | Bei Rückgängig geht eine Korrekturnachricht an die Empfänger | Nachrichtentyp „Korrektur“ |
| Linkarten | Team-Einladungslink (Mitglied) und Termin-Gastlink (Gast ohne Konto) | Zwei Berechtigungsmodelle, Widerruf |
| Linkablauf | Einladung widerrufbar; Gastlink gültig bis Terminende + 30 Tage | Ablauf-Job |
| Gast → Konto | Gast kann bei Registrierung über denselben Link sein bisheriges Handeln übernehmen | Zuordnungslogik, Datenschutzprüfung |
| KI-Anbieter | Anbieterneutrale Schnittstelle, Start mit Claude | Abstraktionsschicht, AV-Vertrag |
| KI-Kosten | Monatslimit je Team, Betreiber trägt; Anzeige über Kostenerfassung (F-018) | Limitverwaltung |
| Gast-Sprache | Browsersprache, umschaltbar, Fallback Deutsch; Benachrichtigungen in gespeicherter Sprache | Sprache am Gast speichern |
| Erinnerungen | Zeitpunkte stellt der Benutzer selbst ein. Über den Assistenten sind abweichende Zeiten je Termin möglich, die nur für diesen Benutzer gelten | Erinnerungen als Benutzer-Einstellung mit Termin-Override je Benutzer; keine Leitungs-Vorgabe |
| Schulferien | Öffentliche API (z. B. OpenHolidays) mit Cache | Abhängigkeit, Cache |
| Mailversand | Eigener SMTP-Relay bzw. EU-Anbieter | SPF/DKIM betreuen |
| Datenbank | Keine Randbedingung, wird in der Architektur (arc42) entschieden. Ziel: tägliches verschlüsseltes externes Backup | Datenbank aus RA-008 streichen, Backup-Ziel bleibt offen |
| Umgebungen | Zwei Umgebungen im geteilten Cluster: prod (bisheriges System) und staging (Entwicklung/Test). Später wird prod umgestellt | Datenmigration zuerst in staging testen |
| Keycloak | Bereits vorhandene Instanz weiternutzen | Abhängigkeit von deren Verfügbarkeit |
| Recht | Product Owner ist Datenschutzverantwortlicher; Standardtexte Impressum/Datenschutz in DE/EN | Texte rechtlich prüfen |
| Qualitätsziele | RPO 24 h, RTO 8 h, Seitenantwort < 1 s, Zustellquote > 95 % (Antwortquote und Mindestbreiten bleiben offen) | QA-Dateien ergänzen |
| Projekt | Roadmap nach Wert: Kern (Teams, Termine, Rückmeldung) zuerst, Datenmigration vor Prod-Umstellung | Konkreter Zeitplan, Budget, Vertretung bleiben offen |

**Weiterhin offen:** Datenschutz beim KI-Anbieter im Detail, Messenger-Auswahl, Backup-Ziel, Antwortquote, Mindestbreiten, Zeitplan/Budget/Vertretung.

## Wirkung
RA-008 schrumpft auf die genannten Restpunkte. Die zugehörigen Features (F-001, F-005, F-006, F-009, F-012, F-015, F-017, F-018) und QA-Dateien bekommen die Entscheidungen.

## Entscheidung (Mensch)
