---
title: Randbedingungen
status: entwurf
quellen: [req42 RB-001..RB-011, BM-001, RA-009]
---

# Kapitel 2: Randbedingungen

Alles hier ist **Vorgabe** (aus req42), keine Architekturentscheidung. RB-007 ist entfallen.

## Technische Randbedingungen

| Randbedingung | Folge für die Architektur | Quelle |
|---|---|---|
| Betrieb containerisiert auf geteiltem k3s (3 Nodes: 1× 4 vCPU/8 GB, 2× 2 vCPU/4 GB); Umgebungen prod und staging | Lauffähig als Container; keine Annahmen über exklusive Hardware. | [RB-005](../../req42/07-randbedingungen/RB-005-betrieb-auf-geteiltem-k3s-cluster.md), [BM-001](../../req42/09-betriebsmittel-personal/BM-001-laufzeitumgebung.md) |
| Ressourcenbudget ca. 1 vCPU / 1 GiB RAM für alle Chronos-Komponenten inkl. Datenbank und Hintergrundverarbeitung (?), besser weniger | Technologien mit hohem Grundspeicher (z. B. JVM-Stack) sind zu begründen. | [RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md) |
| Identität ausschließlich über den vorhandenen, geteilten Keycloak (nicht im Budget); keine eigene Passwortverwaltung; Gäste haben keine Keycloak-Identität | Anmeldung delegiert; Gast ist ein eigenes Konzept in Chronos. | [RB-002](../../req42/07-randbedingungen/RB-002-identitaetsdienst-keycloak.md) |
| Web-Anwendung, mobil zuerst, Mindestbreite 320 px | Responsive Oberfläche; Web Push setzt browserseitige Unterstützung voraus (nicht überall zuverlässig, [RA-006](../../req42/12-risiken-annahmen/RA-006-zustellung-ueber-web-push-ist-unsicher.md)). | [QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md) |
| Standards: iCalendar und RRULE (RFC 5545), webcal, Web Push | Standardkonforme Ein-/Ausgabe, volle RRULE-Unterstützung. | [FA-009](../../req42/04-product-backlog/anforderungen/FA-009-kalender-feed.md), [FA-014](../../req42/04-product-backlog/anforderungen/FA-014-serientermine.md) |
| Backup täglich, clientseitig verschlüsselt, in S3-kompatiblen EU-Objektspeicher | Backup-Format und Schlüsselverwaltung sind in Chronos' Verantwortung. | [QA-006](../../req42/06-qualitaet/QA-006-datensicherung.md), [BM-001](../../req42/09-betriebsmittel-personal/BM-001-laufzeitumgebung.md) |
| Mailversand über SMTP-Relay oder EU-Anbieter | E-Mail ist ein kostenpflichtiger Kanal. | [BM-001](../../req42/09-betriebsmittel-personal/BM-001-laufzeitumgebung.md) |

## Organisatorische Randbedingungen

| Randbedingung | Folge | Quelle |
|---|---|---|
| Datenübernahme aus chronos-root (Benutzer, Termine mit Rückmeldungen, Gruppen → Teams, Terminnachrichten), wiederholbar; Freundschaften entfallen | Datenmodell und Architektur sind daran zu prüfen. | [RB-004](../../req42/07-randbedingungen/RB-004-datenuebernahme-aus-chronos-root.md), [M-005](../../req42/05-modelle/M-005-migrationsabbildung.md) |
| Oberfläche **und** Benachrichtigungen mehrsprachig (zunächst DE/EN), weitere Sprachen ohne Umbau | Texte nicht im Code verstreut. | [RB-001](../../req42/07-randbedingungen/RB-001-mehrsprachigkeit.md) |
| Vollständige, UI-unabhängige Operationsschicht; schreibende Assistent-Operationen mit Vorschau und Freigabe | Zentrale Strukturvorgabe. | [RB-011](../../req42/07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md) |
| Kosten je Benutzer, sonst Team, als rekonstruierbare Einzelposten, auch Fehlversuche | Jeder kostenverursachende Aufruf läuft über eine erfassende Stelle. | [RB-010](../../req42/07-randbedingungen/RB-010-kostenzuordnung.md) |
| Zusatzkosten höchstens 10 €/Monat (ohne Cluster und Personal); bei Erreichen pausiert die KI, Backup und E-Mail laufen weiter | Limit-Prüfung vor KI-Aufrufen. | [RA-009](../../req42/12-risiken-annahmen/RA-009-budget-und-abhaengigkeit-von-keycloak.md) |
| DSGVO, Impressum; keine Daten von Kindern und Eltern; Product Owner ist Verantwortlicher | Datensparsamkeit im Modell; Datenschutzerklärung deckt sich mit der Verarbeitung. | [RB-006](../../req42/07-randbedingungen/RB-006-datenschutz-und-impressum.md) |
| Keine Geheimnisse im Repository | Konfiguration und Secrets von außen. | [RB-008](../../req42/07-randbedingungen/RB-008-keine-geheimnisse-im-repository.md) |
| Wissen im `wiki/`, kein Agenten-Gedächtnis; `docs/` nur mit menschlicher Freigabe | Arbeitsweise, kein Systementwurf. | [RB-009](../../req42/07-randbedingungen/RB-009-wissen-im-wiki.md), [docs/README](../../README.md) |
| Ein-Personen-Team plus Agenten, keine benannte Vertretung | Einfachheit und Dokumentation vor Eleganz. | [TS-001](../../req42/10-teamstruktur/TS-001-rollen-und-zusammenarbeit.md), [RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md) |

## Konventionen

- Deutsch in Dokumentation und Oberfläche; Code-Namen englisch (Zuordnung: [Glossar](../../req42/08-terminologie/glossar.md)).
- Dokumente mit `status: entwurf | freigegeben` im Frontmatter; IDs sind stabil, nie umnummerieren.
- Tickets nach [ticket-typen](../../req42/04-product-backlog/ticket-typen.md).
- Entwicklungsprozess (Branches, PR-Regeln, Prüfungen) ist bewusst **keine** Randbedingung und wird später festgelegt.
