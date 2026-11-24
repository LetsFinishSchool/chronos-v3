---
title: Lösungsstrategie
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 QA-*, RB-*, Z-*]
---

# Kapitel 4: Lösungsstrategie

Diese Seite hält fest, **welche Strategie die Anforderungen erzwingen** und **welche Entscheidungen noch fehlen**. Entschieden (im Entwurf) sind nur Rangfolge der Qualitätsziele und Zerlegung ([ADR-001](../09-entscheidungen/ADR-001-prioritaet-der-qualitaetsziele.md), [ADR-002](../09-entscheidungen/ADR-002-zerlegung-monolith-plus-worker.md)); Technologie und Mechanismen sind offen ([Kapitel 9](../09-entscheidungen/01-offene-entscheidungen.md)).

## Qualitätsziel → Ansatz

| Qualitätsziel | Zwingender Ansatz (aus req42) | Offen |
|---|---|---|
| Änderbarkeit ([QA-003](../../req42/06-qualitaet/QA-003-aenderbarkeit.md)) | Fachbereiche klar getrennt und abstrahiert; Abhängigkeitsregeln automatisch prüfbar (Architekturtests); Kanäle, Terminarten und Sprachen sind Erweiterungspunkte, keine Verzweigungen im Fachcode. | Zerlegung: [ADR-002](../09-entscheidungen/ADR-002-zerlegung-monolith-plus-worker.md) (Monolith plus Worker) |
| Gleiche Fähigkeiten für UI und Assistent ([RB-011](../../req42/07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md)) | Eine vollständige, UI-unabhängige **Operationsschicht**; UI und Assistent sind gleichrangige Clients. Eine neue Fachfunktion erscheint ohne Zusatzaufwand beim Assistenten. | Form der Schicht (E-005) |
| Nachvollziehbarkeit ([QA-002](../../req42/06-qualitaet/QA-002-nachvollziehbarkeit.md)) | Fachliche **Ereignisse** sind explizite Objekte mit benanntem Auslöser, keine Nebenwirkungen. Korrelations-ID von der Anfrage bis zur Zustellung. | Ereignismechanismus (E-006) |
| Zuverlässige Benachrichtigung ([QA-004](../../req42/06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md)) | Ein Ereignis wird **dauerhaft festgehalten**, bevor es zugestellt wird; Zustellung höchstens einmal je Empfänger und Kanal; begrenzte Wiederholung; Ersatzkanal E-Mail. | Mechanismus, Scheduler (E-006) |
| Sparsame Benachrichtigung ([QA-010](../../req42/06-qualitaet/QA-010-benachrichtigungsbudget.md)) | Erinnerungen und Sammelmeldungen werden **geplant und gebündelt**, keine harte Laufzeitsperre. | Planungsverfahren (E-006) |
| Rückgängig für alles ([F-017](../../req42/04-product-backlog/features/F-017-rueckgaengig-machen.md)) | Jede schreibende Operation hinterlässt einen Verlaufseintrag mit Vorher-Zustand und Bündel-ID; 30 Tage Wiederherstellung gelöschter Objekte. | Mechanismus (E-007) |
| Kostentransparenz ([RB-010](../../req42/07-randbedingungen/RB-010-kostenzuordnung.md)) | Alle kostenverursachenden Aufrufe laufen über **eine** erfassende Stelle; Limit-Prüfung davor. | – |
| Ressourceneffizienz ([QA-001](../../req42/06-qualitaet/QA-001-ressourceneffizienz.md)) | Wenige Prozesse, kein Grundspeicher ohne Begründung; Datenbank und Hintergrundverarbeitung zählen zum Budget (?). | Sprache, Laufzeit, DB (E-002, E-003) |
| Mobil, Zugang ohne Hürde ([QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md)) | Gast ist eine eigene Person-Art; Link-Antwort ohne Konto; Oberfläche mobil zuerst. | Frontend (E-004), Gastkonzept (E-008) |
| Datenübernahme ([RB-004](../../req42/07-randbedingungen/RB-004-datenuebernahme-aus-chronos-root.md)) | Modell an [M-005](../../req42/05-modelle/M-005-migrationsabbildung.md) prüfen; Übernahme wiederholbar und abgleichbar. | Durchführung (E-017) |
| Sicherheit und Datenschutz ([QA-007](../../req42/06-qualitaet/QA-007-sicherheit-und-datenschutz.md)) | Nicht erratbare, widerrufbare Token; Datensparsamkeit im Modell; keine Daten von Kindern/Eltern. | – |

## Strategische Leitlinien (abgeleitet, nicht technologisch)

1. **Fachlichkeit vor Technik:** Das Fachmodell ([M-001](../../req42/05-modelle/M-001-fachdatenmodell.md)) ist der Kern; Kanäle, Anbieter und Oberfläche hängen davon ab, nie umgekehrt.
2. **Explizit statt implizit:** Zustandsänderung → Ereignis → Reaktion; keine versteckten Seiteneffekte.
3. **Ein Weg für alles:** Jede Zustandsänderung läuft durch die Operationsschicht und damit durch Berechtigung, Verlauf, Kostenerfassung und Ereignisbildung.
4. **Erweiterbar an definierten Stellen:** siehe [Veränderlichkeit](02-veraenderlichkeit.md).
5. **Klein halten:** Jede zusätzliche Laufzeitkomponente muss gegen das Budget gerechtfertigt werden.
