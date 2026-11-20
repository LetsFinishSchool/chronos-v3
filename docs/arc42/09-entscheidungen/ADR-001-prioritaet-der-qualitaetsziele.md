---
id: ADR-001
title: Priorisierung der Qualitätsziele
status: angenommen
freigegeben-am: 2026-11-20
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-000]
quellen: [Gespräch mit dem Product Owner 2026-11-20, arc42 1.2]
---

# ADR-001: Priorisierung der Qualitätsziele

## Kontext
Die fünf Qualitätsziele ([1.2](../01-einfuehrung/02-qualitaetsziele.md)) stehen in Spannung zueinander (Budget gegen Änderbarkeit, Zuverlässigkeit gegen Benachrichtigungsbudget). Für Technikwahl und Zerlegung braucht es eine Rangfolge für den Konfliktfall.

## Entscheidung
Rangfolge bei Zielkonflikten:

1. **Änderbarkeit und Modularität** ([QA-003](../../req42/06-qualitaet/QA-003-aenderbarkeit.md))
2. **Bedienbarkeit mobil, Zugang ohne Hürde** ([QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md), [Z-004](../../req42/01-ziele/Z-004-zugang-ohne-huerde.md))
3. **Ressourceneffizienz** ([QA-001](../../req42/06-qualitaet/QA-001-ressourceneffizienz.md), [QA-008](../../req42/06-qualitaet/QA-008-leistung.md))
4. **Zuverlässige, sparsame Benachrichtigung** ([QA-004](../../req42/06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md), [QA-010](../../req42/06-qualitaet/QA-010-benachrichtigungsbudget.md))
5. **Nachvollziehbarkeit** ([QA-002](../../req42/06-qualitaet/QA-002-nachvollziehbarkeit.md), [QA-009](../../req42/06-qualitaet/QA-009-kostentransparenz.md))

## Geltung
Die Rangfolge entscheidet **nur bei echten Konflikten** zwischen Lösungsalternativen. Sie hebt keine Anforderung auf: Alle QA-Szenarien und Randbedingungen (insbesondere RB-003 Budget, RB-010 Kostenerfassung) bleiben Pflicht. Datensicherung (QA-006) und Sicherheit/Datenschutz (QA-007) sind Pflicht und stehen außerhalb der Rangfolge.

## Folgen
- Bei Zielkonflikt gewinnt die modularere Lösung, auch wenn sie etwas mehr Ressourcen braucht, solange das Budget eingehalten wird (E-001, E-002).
- Mobile Bedienbarkeit und Zugang ohne Hürde dürfen nicht für Ressourcen oder Zuverlässigkeitsmechanik geopfert werden (E-004, E-008).
- Nachvollziehbarkeit steht zuletzt: Sie wird nicht für Änderbarkeit, Bedienbarkeit oder Budget aufgegeben, bleibt aber als Anforderung (Auslöser, Korrelations-ID) bestehen. **Auffälligkeit:** Z-002 verlangt 100 % Protokolleinträge mit benanntem Auslöser; diese Pflicht darf nur über das Wie, nie über das Ob verhandelt werden.
- Zuverlässige Benachrichtigung auf Platz 4: Zustellquote > 95 % bleibt Ziel; Mehraufwand für Garantien (Ersatzkanäle, Wiederholung) wird gegen Budget und Einfachheit abgewogen (E-006).

## Wann überprüfen?
Wenn Betrieb oder Nutzer Benachrichtigungsausfälle als Hauptproblem melden, oder das Budget in der Praxis die Änderbarkeit erkennbar verhindert.
