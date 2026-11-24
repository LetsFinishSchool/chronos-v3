---
id: QA-003
title: Änderbarkeit und Modularität
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-005]
---

# QA-003: Änderbarkeit und Modularität

**Qualitätsmerkmal (ISO 25010):** Wartbarkeit (Modifizierbarkeit, Modularität)

## Szenario
(a) Ein neuer Benachrichtigungskanal (z. B. Telegram) wird ergänzt, ohne Ereignislogik zu ändern. (b) Eine neue Terminart wird ergänzt, ohne Benachrichtigung und Rückmeldung anzufassen. (c) Eine neue Fachfunktion steht ohne Zusatzaufwand auch dem KI-Assistenten zur Verfügung ([RB-011](../07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md)). Fachbereiche sind klar getrennt und abstrahiert.

## Messbar durch
Review der Änderung: Anzahl berührter Module; Architekturtests (Abhängigkeitsregeln).
