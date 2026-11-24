---
title: Aufgabenstellung
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 (Z-001..Z-010, F-001..F-018, RB-*, QA-*)]
---

# 1.1 Aufgabenstellung

Chronos ist eine Web-Anwendung für **ehrenamtliche Leitungsteams von Jugendverbänden** ([SH-002](../../req42/02-stakeholder/SH-002-leitungsteam-mitglied.md)). Sie plant interne Termine und Veranstaltungen, holt Rückmeldungen automatisch ein und benachrichtigt zuverlässig und sparsam. Komplexe Aufgaben erledigt ein KI-Assistent, die Weboberfläche bleibt einfach. Chronos ist der Neuanfang (chronos-v3) von chronos-root; dessen Bestandsdaten müssen übernommen werden ([RB-004](../../req42/07-randbedingungen/RB-004-datenuebernahme-aus-chronos-root.md)).

## Funktionsumfang (Kurzfassung)

| Bereich | Features |
|---|---|
| Struktur | Teams und beliebig tiefe Unter-Teams, Mitglieder, Einladungslinks, Labels ([F-001](../../req42/04-product-backlog/features/F-001-teams-und-unter-teams.md), [F-002](../../req42/04-product-backlog/features/F-002-mitglieder-und-einladungslink.md), [F-007](../../req42/04-product-backlog/features/F-007-labels.md)) |
| Planung | Termine (Treffen, Frist/Marke), Veranstaltungen, Serientermine, Terminfindung, Zeitraumsregeln ([F-003](../../req42/04-product-backlog/features/F-003-termine.md), [F-004](../../req42/04-product-backlog/features/F-004-veranstaltungen.md), [F-006](../../req42/04-product-backlog/features/F-006-terminfindung.md), [F-014](../../req42/04-product-backlog/features/F-014-serientermine.md), [F-016](../../req42/04-product-backlog/features/F-016-zeitraumsregeln.md)) |
| Teilnahme | Rückmeldung Zusage/Absage/Zeitweise, automatische Erinnerung ([F-005](../../req42/04-product-backlog/features/F-005-rueckmeldung.md)) |
| Kommunikation | Benachrichtigungen (Web Push, E-Mail, optional Messenger), Kalender-Feed, Terminnachrichten ([F-008](../../req42/04-product-backlog/features/F-008-benachrichtigungen.md), [F-009](../../req42/04-product-backlog/features/F-009-kalender-feed.md), [F-010](../../req42/04-product-backlog/features/F-010-terminnachrichten.md)) |
| Zugang und Recht | Anmeldung über Keycloak, Zugang ohne Konto per Link, rechtliche Seiten ([F-011](../../req42/04-product-backlog/features/F-011-anmeldung-und-konto.md), [F-013](../../req42/04-product-backlog/features/F-013-rechtliche-seiten.md)) |
| Querschnitt | Änderungsverlauf mit Rückgängig, Kostenerfassung, KI-Assistent, Datenübernahme ([F-017](../../req42/04-product-backlog/features/F-017-rueckgaengig-machen.md), [F-018](../../req42/04-product-backlog/features/F-018-kostenerfassung.md), [F-015](../../req42/04-product-backlog/features/F-015-ki-assistent.md), [F-012](../../req42/04-product-backlog/features/F-012-datenuebernahme.md)) |

## Warum der Neuanfang (architekturtreibend)

Aus den Key Learnings des Altsystems chronos-root: Domänenmodell trug nicht, Zugang war zu hoch, Benachrichtigung unzuverlässig und kaum nachvollziehbar, Codebasis schwer pflegbar (intransparenter Datenfluss, schlechte Trennung), RAM-Verbrauch zu hoch. Jeder dieser Punkte ist ein Qualitätsziel ([1.2](02-qualitaetsziele.md)).

## Architekturrelevante Eckwerte

- **Agil, volatil:** Anforderungen kommen und gehen jederzeit. Die Architektur muss Änderung billig machen (siehe [Veränderlichkeit](../04-loesungsstrategie/02-veraenderlichkeit.md)).
- **Klein:** < 500 aktive Nutzer, rund 1 vCPU und 1 GiB RAM für alles ([RA-002](../../req42/12-risiken-annahmen/RA-002-nutzungsumfang.md), [RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md)).
- **Ein-Personen-Team mit Agenten:** Betrieb und Entwicklung müssen schlank bleiben ([TS-001](../../req42/10-teamstruktur/TS-001-rollen-und-zusammenarbeit.md)).
- **Vollständige Operationsschicht:** Jede Funktion muss auch dem Assistenten zur Verfügung stehen, die UI zeigt bewusst weniger ([RB-011](../../req42/07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md)).
- **Datenübernahme** aus chronos-root vor der Produktivschaltung ([RM-001](../../req42/11-roadmaps/RM-001-fundament-mit-datenuebernahme.md)).
