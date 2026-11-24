---
title: Risiken und technische Schulden
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
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

| ID | Risiko | Warum | Maßnahme (Stand) |
|---|---|---|---|
| R-A1 | **Budget gegen Funktionsumfang.** 1 vCPU / 1 GiB für Anwendung, Datenbank, Hintergrundverarbeitung, Beobachtung | Viele Querschnitte (Ereignisse, Verlauf, Kosten, Assistent) kosten Ressourcen | Früher Lasttest; Technikwahl am Budget messen (E-002, E-003) |
| R-A2 | **Operationsschicht wird zum Nadelöhr.** Jede Funktion braucht Beschreibung, Vorschau, Berechtigung, Verlauf | Aufwand je neuer Funktion steigt, wenn die Schicht nicht Vieles automatisch liefert | Rahmen trägt den Querschnitt ([ADR-005](../09-entscheidungen/ADR-005-operationsschicht.md)); Durchstich E-005a zu Beginn der Umsetzung |
| R-A3 | **Wiederherstellung muss alle abhängigen Inhalte umfassen** (Unter-Teams, Rückmeldungen, Labels, Nachrichten) | Unvollständige Wiederherstellung | Soft-Delete im Fachmodell ([K-004](../08-konzepte/K-004-aenderungsverlauf-und-rueckgaengig.md)) |
| R-A4 | **Benachrichtigungsbudget gegen Zuverlässigkeit.** Wiederholung und Ersatzkanal erhöhen die Zahl | Beides sind Ziele | Planung und Bündelung; Messung im Protokoll (E-006, E-014) |
| R-A5 | **Zeitsteuerung ist ungeplant „implizit“.** Viele zeitgesteuerte Auslöser (Erinnerungen, Fristen, Ablauf) | Verstößt sonst gegen explizite Datenflüsse (QA-002) | Zeitauslöser als benannte Auslöser mit Korrelations-ID |
| R-A6 | **Altdaten passen nicht** und der Import hat keine Ereigniswirkung geplant | Import könnte Massenbenachrichtigungen auslösen | Importmodus entschieden (Ereignisse erzeugt, als „importiert“ markiert, nicht zugestellt); Probelauf in staging (E-017) |
| R-A7 | **Unscharfe Anforderungen.** Eine Reihe (?) ist offen (Budget-Umfang, Gastsprache, Externe-Kanäle) | Architektur kann auf Annahmen bauen | [RA-008](../../req42/12-risiken-annahmen/RA-008-offene-fragen.md) abarbeiten |
| R-A8 | **Lösch- und Backup-Konflikt.** 30-Tage-Wiederherstellung und Datenschutzlöschung gegen Backups | Rechtliche Wirkung | Löschkonzept (K-008) |
| R-A9 | **Bibliotheken ohne Pflege in kritischen Pfaden** (`rrule`, `web-push-native`, `chrono-tz` archiviert) | Ausfall oder Sicherheitslücke ohne Behebung | Isolation hinter Schnittstellen, Differenztest RRULE, Plan B `jiff`, `cargo-deny` mit befristeten Ausnahmen ([ADR-004](../09-entscheidungen/ADR-004-sprache-und-laufzeit.md), [ADR-012](../09-entscheidungen/ADR-012-zeitbibliothek.md), [ADR-013](../09-entscheidungen/ADR-013-build-ci-lieferkette.md)) |
| R-A10 | **KI-Gateway falsch konfiguriert, Daten verlassen die EU** | Die EU-Regel wird nur im Gateway durchgesetzt | Positivliste der Basisadressen mit Alarm, Betriebsbedingungen ([ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md)) |
| R-A11 | **Qualität der zulässigen KI-Modelle reicht nicht** | EU-Modelle sind gegen F-015 ungeprüft | Prüfkatalog, Modellwechsel nur nach Prüfkatalog ([ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md)) |
| R-A12 | **Gateway-Ausfall pausiert den Assistenten** | Nachbarsystem im selben Cluster, vom Betreiber gepflegt | Fachfunktionen laufen weiter; Alarm ([ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md)) |
| R-A13 | **Refresh-Tokens in der Datenbank; gesperrte Konten bleiben bei Keycloak-Ausfall angemeldet** | Leck von Datenbank und Schlüssel gäbe Zugriff auf Keycloak-Sitzungen; der Ausfall wird bis zu 7 Tage überbrückt | Verschlüsselung (AEAD) mit Schlüsselrotation, Back-Channel-Logout, Alarm nach einer Stunde fehlgeschlagener Heartbeats ([ADR-008](../09-entscheidungen/ADR-008-sitzung-und-gast-identitaet.md)) |
| R-A14 | **Gastseite als SPA: Inhalt erst nach JavaScript** | QA-008 (unter 1 s) bei kaltem Cache im Mobilnetz | Eingebettete Termindaten, Größenbudget 60 KB, Messung im Build ([ADR-007](../09-entscheidungen/ADR-007-frontend-spa-svelte.md)) |
| R-A15 | **Zweite Werkzeugkette (npm) und Svelte-Hauptversionen** | Lieferkette, Brüche (Svelte 4 zu 5, SvelteKit 2 zu 3) | Versionen festschreiben, framework-freies Paket, Austauschbarkeit der UI-Schicht (V-1 bis V-5, [ADR-007](../09-entscheidungen/ADR-007-frontend-spa-svelte.md)) |
| R-A16 | **Zwei Zeittypen (`jiff`, `chrono`) und zwei Zeitzonendatenbanken** | Fehler bei Sommerzeit-Übergängen an der Grenze | Ein Adapter-Modul, Test der Übergänge ([ADR-012](../09-entscheidungen/ADR-012-zeitbibliothek.md)) |
| R-A17 | **Lieferkettenprüfung blockiert die Arbeit einer Person** | Neue Meldungen und auslaufende Ausnahmen blockieren Merges | Befristete Ausnahmen (90 Tage) mit Vorwarnung 14 Tage vorher ([ADR-013](../09-entscheidungen/ADR-013-build-ci-lieferkette.md)) |
| R-A18 | **Probelauf sperrt bei großen Stapeln** | Die Vorschau hält Sperren | Obergrenze 50 Aufrufe oder 500 Objekte, Durchstich E-005a, Rückfall auf Planen und Anwenden ([ADR-005](../09-entscheidungen/ADR-005-operationsschicht.md)) |
| R-A19 | **Schemaänderung bei rollenden Updates** | Alte und neue Version laufen kurz nebeneinander; Migrationen gehen nur vorwärts | Erweitern, umstellen, aufräumen; Job vor dem Rollout; Backup vor jedem Produktionsrollout ([ADR-011](../09-entscheidungen/ADR-011-migrationswerkzeug.md)) |
| R-A20 | **Fluent: kleineres Ökosystem** | Pflegestand von `fluent-rs` und `@fluent/bundle` und Übersetzungsplattform ungeprüft ▲ | Prüfen vor der Umsetzung ([ADR-010](../09-entscheidungen/ADR-010-uebersetzungen-fluent.md)) |

## Technische Schulden

Keine: Neuanfang, noch kein Code. Bewusst aufgeschobene Entscheidungen stehen in [Kapitel 9](../09-entscheidungen/01-offene-entscheidungen.md).
