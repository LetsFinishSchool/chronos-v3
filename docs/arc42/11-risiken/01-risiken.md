---
title: Risiken und technische Schulden
status: entwurf
quellen: [req42 RA-001..RA-010, arc42 Kapitel 4 bis 8]
---

# Kapitel 11: Risiken und technische Schulden

Fachliche Risiken und Annahmen stehen in [req42/12-risiken-annahmen](../../req42/12-risiken-annahmen/README.md). Hier: ihre Wirkung auf die Architektur, plus Risiken, die erst aus der Architektursicht sichtbar werden.

## Aus req42 mit Architekturwirkung

| Risiko | Wirkung | Gegenmaßnahme (Stand) |
|---|---|---|
| [RA-002](../../req42/12-risiken-annahmen/RA-002-nutzungsumfang.md) < 500 Nutzer | Kapazitätsplanung; Lastspitzen (viele Antworten nach Einladung) unbekannt | Lasttest mit 500 Nutzern (QA-001) |
| [RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md) Eine Person | Einfachheit vor Eleganz; Dokumentation im Wiki | akzeptiertes Restrisiko, keine Vertretung |
| [RA-004](../../req42/12-risiken-annahmen/RA-004-gleichberechtigung-und-versehentliche-aenderungen.md) Gleichberechtigung | Gelöschtes muss wiederherstellbar sein | [K-004](../08-konzepte/K-004-aenderungsverlauf-und-rueckgaengig.md) |
| [RA-005](../../req42/12-risiken-annahmen/RA-005-migration-altmodell-passt-nicht.md) Altmodell passt nicht | Modellentscheidungen können an Altdaten scheitern | [K-010](../08-konzepte/K-010-datenuebernahme.md); Altschema früh prüfen |
| [RA-006](../../req42/12-risiken-annahmen/RA-006-zustellung-ueber-web-push-ist-unsicher.md) Web Push unsicher | Ersatzkanal E-Mail Pflicht | [K-003](../08-konzepte/K-003-ereignisse-und-benachrichtigung.md) |
| [RA-007](../../req42/12-risiken-annahmen/RA-007-einladungslinks-und-gast-identitaet.md) Links und Gast-Identität | Weitergabe oder Raten führt zu falschen Antworten | Token, Widerruf, Ablauf ([K-002](../08-konzepte/K-002-berechtigung-und-zugang.md)) |
| [RA-009](../../req42/12-risiken-annahmen/RA-009-budget-und-abhaengigkeit-von-keycloak.md) Budget, Keycloak | Technikwahl begrenzt; bei Keycloak-Ausfall keine Neuanmeldung | Gäste bleiben nutzbar; Limit-Mechanik ([K-005](../08-konzepte/K-005-kostenerfassung.md)) |
| [RA-010](../../req42/12-risiken-annahmen/RA-010-ki-assistent-risiken.md) KI-Risiken | Falsche Aktion, Kosten, Prompt-Injection | Freigabe, Rechte der Person, Wiederherstellung, Limit ([K-006](../08-konzepte/K-006-operationsschicht-und-assistent.md)) |

## Aus der Architektursicht

| ID | Risiko | Warum | Mögliche Maßnahme (nicht entschieden) |
|---|---|---|---|
| R-A1 | **Budget gegen Funktionsumfang.** 1 vCPU / 1 GiB für Anwendung, Datenbank, Hintergrundverarbeitung, Beobachtung | Viele Querschnitte (Ereignisse, Verlauf, Kosten, Assistent) kosten Ressourcen | Früher Lasttest; Technikwahl am Budget messen (E-002, E-003) |
| R-A2 | **Operationsschicht wird zum Nadelöhr.** Jede Funktion braucht Beschreibung, Vorschau, Berechtigung, Verlauf | Aufwand je neuer Funktion steigt, wenn die Schicht nicht Vieles automatisch liefert | Gemeinsame Definition (E-005) |
| R-A3 | **Wiederherstellung muss alle abhängigen Inhalte umfassen** (Unter-Teams, Rückmeldungen, Labels, Nachrichten) | Unvollständige Wiederherstellung | Soft-Delete im Fachmodell ([K-004](../08-konzepte/K-004-aenderungsverlauf-und-rueckgaengig.md)) |
| R-A4 | **Benachrichtigungsbudget gegen Zuverlässigkeit.** Wiederholung und Ersatzkanal erhöhen die Zahl | Beides sind Ziele | Planung und Bündelung; Messung im Protokoll (E-006, E-014) |
| R-A5 | **Zeitsteuerung ist ungeplant „implizit“.** Viele zeitgesteuerte Auslöser (Erinnerungen, Fristen, Ablauf) | Verstößt sonst gegen explizite Datenflüsse (QA-002) | Zeitauslöser als benannte Auslöser mit Korrelations-ID |
| R-A6 | **Altdaten passen nicht** und der Import hat keine Ereigniswirkung geplant | Import könnte Massenbenachrichtigungen auslösen | E-017 früh entscheiden |
| R-A7 | **Unscharfe Anforderungen.** Eine Reihe (?) ist offen (Budget-Umfang, Gastsprache, Externe-Kanäle) | Architektur kann auf Annahmen bauen | [RA-008](../../req42/12-risiken-annahmen/RA-008-offene-fragen.md) abarbeiten |
| R-A8 | **Lösch- und Backup-Konflikt.** 30-Tage-Wiederherstellung und Datenschutzlöschung gegen Backups | Rechtliche Wirkung | Löschkonzept (K-008) |

## Technische Schulden

Keine: Neuanfang, noch kein Code. Bewusst aufgeschobene Entscheidungen stehen in [Kapitel 9](../09-entscheidungen/01-offene-entscheidungen.md).
