---
title: Qualitätsziele
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 QA-001..QA-010]
---

# 1.2 Qualitätsziele

Die folgenden fünf Ziele ergeben sich direkt aus den Gründen für den Neuanfang. **Die Reihenfolge bei Zielkonflikten** legt [ADR-001](../09-entscheidungen/ADR-001-prioritaet-der-qualitaetsziele.md) fest (Entwurf): 1 Änderbarkeit, 2 Bedienbarkeit, 3 Ressourceneffizienz, 4 Benachrichtigung, 5 Nachvollziehbarkeit. Die Tabelle unten ist in dieser Reihenfolge zu lesen, ist aber noch nach Themen gruppiert.

| Qualitätsziel | Bedeutung für die Architektur | req42 |
|---|---|---|
| **Änderbarkeit und Modularität** | Neue Kanäle, Terminarten, Funktionen und Sprachen ohne Eingriff in unbeteiligte Bereiche; neue Funktionen stehen automatisch dem Assistenten zur Verfügung. | [QA-003](../../req42/06-qualitaet/QA-003-aenderbarkeit.md), [Z-005](../../req42/01-ziele/Z-005-schlank-betreiben-und-leicht-weiterentwickeln.md) |
| **Ressourceneffizienz** | Alle Komponenten zusammen ≤ 1 vCPU / 1 GiB RAM bei < 500 Nutzern; Seite < 1 s. | [QA-001](../../req42/06-qualitaet/QA-001-ressourceneffizienz.md), [QA-008](../../req42/06-qualitaet/QA-008-leistung.md) |
| **Nachvollziehbarkeit** | Jede Benachrichtigung ist auf ihren Auslöser rückführbar; Datenfluss explizit, Korrelations-ID durchgängig. | [QA-002](../../req42/06-qualitaet/QA-002-nachvollziehbarkeit.md), [QA-009](../../req42/06-qualitaet/QA-009-kostentransparenz.md) |
| **Zuverlässige, sparsame Benachrichtigung** | Kein Ereignis geht verloren, höchstens eine Zustellung je Empfänger und Kanal, Zustellquote > 95 %, Standard höchstens 2 × Termine der Woche. | [QA-004](../../req42/06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md), [QA-010](../../req42/06-qualitaet/QA-010-benachrichtigungsbudget.md) |
| **Bedienbarkeit mobil, Zugang ohne Hürde** | Mobil zuerst (ab 320 px), Antwort per Link in ≤ 3 Interaktionen. | [QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md), [Z-004](../../req42/01-ziele/Z-004-zugang-ohne-huerde.md) |

Weitere Qualitätsanforderungen (Datensicherung [QA-006](../../req42/06-qualitaet/QA-006-datensicherung.md), Sicherheit und Datenschutz [QA-007](../../req42/06-qualitaet/QA-007-sicherheit-und-datenschutz.md)) gelten als Pflicht, nicht als Abwägungsgröße. Alle Szenarien: [Kapitel 10](../10-qualitaet/02-szenarien.md).

**Spannungen, die Entscheidungen brauchen:** Ressourceneffizienz gegen Technikwahl ([RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md)); Zuverlässigkeit (Wiederholung, Ersatzkanal) gegen Benachrichtigungsbudget.
