---
title: K-005 Kostenerfassung
status: entwurf
quellen: [req42 RB-010, FA-018, QA-009, RA-009, FA-015]
---

# K-005: Kostenerfassung

**Vorgaben:**

- Jeder kostenverursachende Aufruf (E-Mail, Messenger, KI) erzeugt einen **Einzelposten**: Benutzer oder Team, Auslöser, Anbieter, Zeitpunkt, Menge, Betrag ([FA-018](../../req42/04-product-backlog/anforderungen/FA-018-kostenerfassung.md)).
- Zuordnung: Benutzer; ist das unmöglich, Team. **Unzuordenbare Posten gibt es nicht.**
- Auch fehlgeschlagene, aber berechnete Aufrufe werden erfasst.
- Summen sind in Einzelposten aufschlüsselbar und auf die auslösende Aktion rückführbar; Summe der Posten = Anbieterrechnung ([QA-009](../../req42/06-qualitaet/QA-009-kostentransparenz.md)).
- **Limits:** Monatslimit je Team für KI; Gesamtobergrenze 10 €/Monat Zusatzkosten. Bei Erreichen pausiert die KI bis Monatsende, Backup und E-Mail laufen weiter, der Betreiber wird benachrichtigt ([RA-009](../../req42/12-risiken-annahmen/RA-009-budget-und-abhaengigkeit-von-keycloak.md)). Kosten trägt der Betreiber.

**Architekturfolge:** Kostenverursachende Adapter (Kanäle, KI-Anbieter) sind nur über die Kostenerfassung erreichbar (Abhängigkeitsregel 4, [Bausteinsicht](../05-bausteine/01-bausteinsicht.md)). Der Auslöser kommt aus dem Ereignis bzw. der Operation und ist daher ohne Zusatzaufwand verfügbar.

**Entschieden (PO 2026-11-20):** Preise stammen aus der Anbieterantwort; Kosten sind daher erst nach dem Aufruf bekannt, das Limit kann im Einzelfall geringfügig überschritten werden.

**Entschieden (PO 2026-11-20):** Nur EUR, Beträge ganzzahlig in Cent bzw. Bruchteilen; Fremdwährungen sind beim Erfassen umzurechnen.

**Entschieden (PO 2026-11-20):** Anbieter ohne Preis in der Antwort werden mit pauschalen Tarifen im System erfasst.

**Entschieden (PO 2026-11-20):** Kein Abgleich mit der Rechnung vorgesehen; Abweichungen zwischen Tarif und Rechnung bleiben unsichtbar.
