---
id: ADR-006
title: KI-Anbindung über Gateway, nur EU-Datenstandort
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-23
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-009]
quellen: [E-009-ki-anbindung-analyse, F-015, FA-015, FA-018, RA-009, RA-010, K-005, K-006, K-008, ADR-002, ADR-004, ADR-005, Claude-, Mistral-, IONOS-, STACKIT- und LiteLLM-Dokumentation (abgerufen 2026-11-23), Entscheidung des Product Owners 2026-11-23]
---

# ADR-006: KI-Anbindung über Gateway, nur EU-Datenstandort

## Kontext
Der Assistent ([F-015](https://github.com/LetsFinishSchool/chronos-v3/issues/80), [FA-015](https://github.com/LetsFinishSchool/chronos-v3/issues/80)) soll jede Operation aufrufen können, schreibend nur nach Vorschau und Freigabe ([ADR-005](ADR-005-operationsschicht.md)). Er ist anbieterneutral, kostenerfasst mit Einzelposten ([K-005](../08-konzepte/K-005-kostenerfassung.md)), limitiert je Team und durch 10 €/Monat Zusatzkosten insgesamt ([RA-009](../../req42/12-risiken-annahmen/RA-009-budget-und-abhaengigkeit-von-keycloak.md)) und anfällig für Prompt-Injection ([RA-010](../../req42/12-risiken-annahmen/RA-010-ki-assistent-risiken.md)). Für Rust gibt es kein offizielles SDK ([ADR-004](ADR-004-sprache-und-laufzeit.md)). Der Product Owner will Modell und Anbieter **zur Laufzeit ohne Codeänderung** wechseln und betreibt bereits ein LiteLLM-Gateway. Die Anthropic-API bietet keine Verarbeitung nur in der EU (`inference_geo`: nur `global` oder `us`).

## Optionen
Ausführlich in der [Analyse](E-009-ki-anbindung-analyse.md): V1 schlank (ein Aufruf, ohne Schleife und Gespräch), V2 Assistent im Server mit eigenem Client je Anbieter, **V2-G** wie V2 über das vorhandene LiteLLM-Gateway, V3 EU zuerst über eigene Adapter je Plattform. Dazu ein Preis- und Bedingungsvergleich europäischer Anbieter (Mistral, IONOS, STACKIT; Scaleway und OVHcloud ungeprüft).

## Entscheidung (PO, 2026-11-23)
**V2-G, und nur Anbieter mit garantiertem europäischem Datenstandort.**

1. **Gateway:** Chronos spricht ausschließlich mit dem LiteLLM-Gateway des Betreibers, im OpenAI-Format (`/chat/completions`), unter einem festen Modellnamen je Umgebung (Alias, z. B. `chronos-assistant`) mit eigenem virtuellen Schlüssel. Modell und Anbieter werden im Gateway gewechselt (Modelle in der Datenbank des Gateways, `STORE_MODEL_IN_DB`), nicht in Chronos.
2. **Client:** eigener schmaler Client (`reqwest`, `serde`) hinter der Schnittstelle `AiProvider` mit genau einem Adapter „OpenAI-kompatibel“. Die Schnittstelle bleibt, damit das Gateway austauschbar ist.
3. **Datenstandort:** Hinter dem Alias dürfen nur Anbieter stehen, die Verarbeitung **und** Speicherung von Gesprächsinhalten in der EU vertraglich oder in ihrer Dokumentation zusichern. Nach dem Stand vom 2026-11-23 erfüllt das: **Mistral über den EU-Endpunkt** (`api.eu.mistral.ai`) und **IONOS AI Model Hub** (nur Deutschland). **Nicht zulässig:** die Anthropic-API direkt (nur `global`/`us`), Mistral über den globalen Endpunkt. **Erst nach Nachweis zulässig:** STACKIT, Scaleway, OVHcloud, Claude über eine Cloud-Plattform in einer EU-Region.
4. **Assistent als eigener Baustein im Web-Prozess** (Client der Operationsschicht, keine Operation), Schleife im Server: lesende Operationen ruft das Modell selbst auf, schreibende werden ein Stapel mit Vorschau und Freigabe-Beleg nach ADR-005. Synchron je Nachricht, mit Deckeln für Runden, Tokens und Zeit.
5. **Gespräch im Server**, Aufbewahrung 24 h nach der letzten Nachricht, durch die Person löschbar.
6. **Kosten und Limit:** vor jedem Aufruf Teamlimit und Gesamtgrenze prüfen; nach dem Aufruf den Betrag aus `x-litellm-response-cost` als Einzelposten buchen (in EUR umgerechnet; Tarif in Chronos nur als Rückfall, wenn der Kopf fehlt), mit dem tatsächlich genutzten Modell (`x-litellm-model-id`). Ausgabengrenze am virtuellen Schlüssel als zweite Linie. Prompt-Caching, wo der Anbieter es kann.
7. **Modell:** konfigurierbar im Gateway; der Standard wird nach einem **Prüfkatalog** typischer Aufgaben festgelegt. Erste Kandidaten: Mistral Small 4 (EU), Mistral Large 4 (EU), IONOS gpt-oss-120b.

Gründe: Der Wechsel von Modell und Anbieter zur Laufzeit ist mit dem Gateway Konfiguration statt Code. In Chronos bleibt ein einziger, kleiner Adapter statt einem je Anbieter. Die Kosten kommen aus der Antwort, wie K-005 es vorsieht. Das Gateway läuft bereits und kostet keine zusätzliche Ressource. Die EU-Regel ist eine Datenschutzentscheidung des Product Owners als Verantwortlichem.

## Folgen
- **Leichter:** Anbieter- und Modellwechsel ohne Release; kein Rust-SDK nötig; Anbieterschlüssel bleiben im Gateway (RB-008); Verarbeitung in der EU vereinfacht Datenschutzerklärung und Auftragsverarbeitung.
- **Schwerer:** Neues Nachbarsystem: Fällt das Gateway aus, pausiert der Assistent (die Fachfunktionen laufen weiter). Das Gateway gehört in Betrieb, Updates und Absicherung des Betreibers (RA-003). Die zulässigen Modelle sind offene Modelle oder Mistral; ob sie die Aufgaben aus F-015 so gut lösen wie Claude, ist ungeprüft und wird erst mit dem Prüfkatalog sichtbar.
- **Widerspruch zu req42 (aufgelöst):** F-015 und SC-001 sagten „Start mit Claude“, was mit der EU-Regel nicht vereinbar war. Beide sind angepasst ([F-015](https://github.com/LetsFinishSchool/chronos-v3/issues/80), [SC-001](../../req42/03-scope/SC-001-systemkontext.md)).
- **Risiken (Kapitel 11):** Neu: „KI-Gateway falsch konfiguriert, Daten verlassen die EU“ und „Qualität der zulässigen Modelle reicht nicht“. Maßnahmen siehe unten.
- **Bindet:** K-006 (Anbieter), Kapitel 3 (Gateway als Nachbar), Kapitel 5 (Assistent im Web-Prozess), K-008 (Gesprächsdaten mit 24 h Löschfrist).

## Bedingungen für den Betrieb
1. **Gateway selbst in der EU** und nicht öffentlich erreichbar; Version aktuell halten.
2. **Fallbacks** nur auf ebenfalls zulässige Ziele (EU-Regel), sonst aus.
3. **Keine Gesprächsinhalte im Gateway speichern:** `store_prompts_in_spend_logs` aus (auch den Schalter in der Oberfläche), keine Protokoll-Callbacks an Dritte.
4. **Virtueller Schlüssel je Umgebung** mit Zugriff nur auf den eigenen Alias und einer Ausgabengrenze unter der Gesamtgrenze.
5. **Prüfung in Chronos:** Chronos vergleicht die Basisadresse des Anbieters aus der Antwort (`x-litellm-model-api-base`) mit einer Positivliste zulässiger EU-Endpunkte. Bei Abweichung pausiert der Assistent und der Betreiber wird benachrichtigt. Das erkennt eine Fehlkonfiguration nach dem ersten Aufruf; es verhindert ihn nicht.
6. **Modellwechsel nur nach Prüfkatalog**, zuerst in staging.
7. **Mistral:** Zero Data Retention beantragen und die Trainingsnutzung der API-Daten prüfen; den AV-Vertrag lesen. Verwaltungsdaten (Konto, Abrechnung, Nutzungsmetadaten) können laut Mistral außerhalb der Region liegen; Gesprächsinhalte nicht.

## Noch festzulegen (ohne neue Entscheidung; Werte siehe „Festgelegte Werte“)
1. Anteil der KI an den 10 €/Monat und Monatslimit je Team.
2. Standardmodell nach dem ersten Prüflauf.
3. Gäste ohne Zugang zum Assistenten (F-015 „nicht (?)“), hier als Annahme.
4. Ort und Version des Gateways, `STORE_MODEL_IN_DB` aktiv, Mitnutzung durch andere Anwendungen.

## Festgelegte Werte (PO, 2026-11-24)
1. **Budget:** KI-Gesamtgrenze 5 €/Monat (Hälfte der 10 € Zusatzkosten), Limit je Team 1 €/Monat. Die Aufteilung ist eine Schätzung ▲ (Grundlage: grob 5.000 Eingabe- und 1.000 Ausgabetoken je Runde, Mistral Small 4 etwa 0,001 €, Large 4 etwa 0,006 € je Runde) und gegen [RB-003](../../req42/07-randbedingungen/) zu prüfen.
2. **Standardmodell:** vorläufig Mistral Small 4; endgültig erst nach dem Prüflauf; Mistral Large 4 ist die Rückfallebene.
3. **Prüfkatalog:** etwa 20 Aufgaben aus F-015, dazu Prompt-Injection-Fälle, Antwortsprache und „nie schreiben ohne Vorschau“. Bestanden bei mindestens 90 % der Aufgaben und 100 % der Sicherheitsfälle (Startwert ohne Messbasis).
4. **Gäste** haben keinen Zugang zum Assistenten (kein Konto, keine zuordenbaren Kosten, größere Angriffsfläche, RA-010).
5. **Gateway:** bestehender LiteLLM-Proxy des Betreibers in der EU, Version fest gepinnt, `STORE_MODEL_IN_DB` aktiv, eigener virtueller Schlüssel je Umgebung, Mitnutzung durch andere Anwendungen nur mit eigenem Schlüssel und Budget; ein Test sichert die ausgewerteten `x-litellm-*`-Header. **Ort:** im selben Cluster wie Chronos (Angabe des Betreibers 2026-11-24); Betriebsbedingung 1 („Gateway in der EU“) setzt einen EU-Standort des Clusters voraus, der vom Betreiber am 2026-11-24 bestätigt wurde (Gateway läuft in der EU). **Version:** die aktuelle LiteLLM-Version; die konkrete Nummer wird beim Festschreiben (Pin) hier eingetragen.

## Wann überprüfen?
- Wenn Anthropic (oder eine Cloud-Plattform mit Claude) einen garantierten EU-Standort anbietet: Claude wird zulässig, ohne Codeänderung.
- Wenn kein zulässiges Modell den Prüfkatalog besteht.
- Wenn das Gateway wegfällt oder nicht mehr gepflegt wird: Ersatz durch einen Adapter je Anbieter (V2) hinter derselben Schnittstelle.
- Wenn die Kosten je Aufgabe das Budget sprengen.
