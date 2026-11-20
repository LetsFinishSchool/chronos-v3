---
title: Qualitätsszenarien
status: entwurf
quellen: [req42 QA-001..QA-010]
---

# 10.2 Qualitätsszenarien

Maßgeblich sind die Szenarien in [req42/06-qualitaet](../../req42/06-qualitaet/README.md). Hier steht die Verbindung zur Architektur: **wo** ein Szenario in arc42 verankert ist und **womit** es geprüft wird.

| ID | Kernaussage | Messgröße / Prüfung | Verankert in |
|---|---|---|---|
| [QA-001](../../req42/06-qualitaet/QA-001-ressourceneffizienz.md) | ≤ 1 vCPU / 1 GiB für alle Komponenten bei < 500 Nutzern | Cluster-Metriken, Lasttest 500 Nutzer | [Strategie](../04-loesungsstrategie/01-loesungsstrategie.md), [Verteilung](../07-verteilung/01-verteilungssicht.md) |
| [QA-002](../../req42/06-qualitaet/QA-002-nachvollziehbarkeit.md) | Auslöser jeder Benachrichtigung in Minuten ermittelbar | Stichprobe; Korrelations-ID durchgängig | [K-003](../08-konzepte/K-003-ereignisse-und-benachrichtigung.md), [K-009](../08-konzepte/K-009-beobachtbarkeit.md) |
| [QA-003](../../req42/06-qualitaet/QA-003-aenderbarkeit.md) | Neuer Kanal, neue Terminart, neue Funktion mit geringer Modulberührung | Review: Anzahl berührter Module; Architekturtests | [Veränderlichkeit](../04-loesungsstrategie/02-veraenderlichkeit.md), [Abhängigkeitsregeln](../05-bausteine/01-bausteinsicht.md) |
| [QA-004](../../req42/06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md) | Nichts verloren, höchstens eine Zustellung je Empfänger und Kanal | Test mit Neustart während des Versands; Zustellquote > 95 % | [K-003](../08-konzepte/K-003-ereignisse-und-benachrichtigung.md), [L-2](../06-laufzeit/01-laufzeitszenarien.md) |
| [QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md) | Kernabläufe mobil ab 320 px; Link-Antwort ≤ 3 Interaktionen | Usability-Test | [L-1](../06-laufzeit/01-laufzeitszenarien.md) |
| [QA-006](../../req42/06-qualitaet/QA-006-datensicherung.md) | RPO 24 h, RTO 8 h | Regelmäßiger Wiederherstellungstest | [Verteilung](../07-verteilung/01-verteilungssicht.md) |
| [QA-007](../../req42/06-qualitaet/QA-007-sicherheit-und-datenschutz.md) | Nicht erratbare, widerrufbare Token; Datensparsamkeit | Sicherheitstests der Token; Abgleich mit Datenschutzerklärung | [K-002](../08-konzepte/K-002-berechtigung-und-zugang.md), [K-008](../08-konzepte/K-008-sicherheit-und-datenschutz.md) |
| [QA-008](../../req42/06-qualitaet/QA-008-leistung.md) | Seite < 1 s bei < 500 Nutzern | Lasttest | [Strategie](../04-loesungsstrategie/01-loesungsstrategie.md) |
| [QA-009](../../req42/06-qualitaet/QA-009-kostentransparenz.md) | Jeder kostenverursachende Aufruf ist ein rückführbarer Posten | Stichprobe von zehn Posten; Summe = Rechnung | [K-005](../08-konzepte/K-005-kostenerfassung.md) |
| [QA-010](../../req42/06-qualitaet/QA-010-benachrichtigungsbudget.md) | Standard ≤ 2 × Termine der Woche je Person | Auswertung des Zustellprotokolls | [K-003](../08-konzepte/K-003-ereignisse-und-benachrichtigung.md), [L-3](../06-laufzeit/01-laufzeitszenarien.md) |

**Lücke:** Für QA-008 ist die Randbedingung „Standardaktionen“ im Anforderungstext noch unscharf formuliert (der Satz in req42 bricht ab). Der Zielwert „Seite < 1 s“ ist durch den Product Owner entschieden; die Zuordnung der Aktionen ist zu präzisieren.
