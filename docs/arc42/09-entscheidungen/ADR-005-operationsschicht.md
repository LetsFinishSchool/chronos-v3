---
id: ADR-005
title: Form der Operationsschicht
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-23
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-005]
quellen: [E-005-operationsschicht-analyse, RB-011, FA-015, QA-002, QA-003, K-002, K-004, K-005, K-006, RA-010, ADR-001, ADR-002, ADR-004, Rust-Spike E-002, Entscheidung des Product Owners 2026-11-23]
---

# ADR-005: Form der Operationsschicht

## Kontext
Alle Fachfunktionen liegen hinter einer vollständigen, von der Oberfläche unabhängigen Operationsschicht; Oberfläche und Assistent sind gleichrangige Clients ([RB-011](../../req42/07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md), [K-006](../08-konzepte/K-006-operationsschicht-und-assistent.md)). Jede schreibende Operation braucht eine Vorschau ohne Wirkung, und der Assistent schreibt nur nach Freigabe ([FA-015](../../req42/04-product-backlog/anforderungen/FA-015-ki-assistent.md), [RA-010](../../req42/12-risiken-annahmen/RA-010-ki-assistent-risiken.md)). Berechtigung an einer Stelle ([K-002](../08-konzepte/K-002-berechtigung-und-zugang.md)), Verlauf als Querschnitt mit Akteur und Bündel-ID ([K-004](../08-konzepte/K-004-aenderungsverlauf-und-rueckgaengig.md)), Ereignis in derselben Transaktion (QA-002, E-006). Änderbarkeit hat Rang 1 ([ADR-001](ADR-001-prioritaet-der-qualitaetsziele.md)); Risiko R-A2: Die Schicht wird zum Nadelöhr, wenn sie den Querschnitt nicht selbst liefert. Sprache: Rust ([ADR-004](ADR-004-sprache-und-laufzeit.md)).

Der Rust-Spike belegt „eine Beschreibung erzeugt Endpunkt, Validierung, Operationsliste, KI-Werkzeug und Frontend-Typen“ (1 Datei je neuer Operation). Er prüft aber die Berechtigung in jeder Operation, schreibt Verlauf und Ereignis von Hand, kennt keine Bündel, hat eine Vorschau nur bei 4 von 10 schreibenden Operationen und überlässt die Freigabe dem Client.

## Optionen
Drei Gesamtvarianten aus sechs Teilfragen (T1 bis T6), ausführlich mit Vor- und Nachteilen in der [Analyse](E-005-operationsschicht-analyse.md):

- **V1 Spike härten:** Trait wie im Spike, Querschnitt als Hilfsfunktionen je Operation, eigene Vorschau-Methode, Freigabe im Client, Sammeländerungen als eigene Operationen. Schnell gebaut, aber Berechtigung, Verlauf und Vorschau hängen an Disziplin je Operation.
- **V2 Rahmen trägt den Querschnitt:** Der Rahmen erzwingt Transaktion, Berechtigung, Verlauf, Ereignis, Vorschau und Freigabe; Operationen enthalten nur Fachlogik. Einmaliger Rahmencode (geschätzt 200 bis 400 Zeilen).
- **V3 Schema-first:** wie V2, aber die Beschreibung in YAML/JSON Schema mit Codegenerator. Sprachneutral, aber zwei Artefakte und ein Generator als Eigenbau.

## Entscheidung (PO, 2026-11-23)
**V2: Der Rahmen trägt den Querschnitt.** Im Einzelnen:

1. **Beschreibung (T1-A):** Jede Operation implementiert einen Trait (Name, Beschreibung, lesend/schreibend, `Params`/`Result` mit Schema, Geltungsbereich, Fachlogik) und wird über `inventory` registriert; keine zweite Liste von Hand. Ob `schemars` statt utoipa die Schemaquelle wird (T1-B), klärt die Spike-Erweiterung E-005a; ein Wechsel betrifft nur den Rahmen und würde die Frameworkliste in ADR-004 ändern.
2. **Querschnitt im Rahmen (T2-B):** Der Rahmen öffnet die Transaktion (lesende Operationen als `READ ONLY`), prüft den aus den Parametern abgeleiteten Geltungsbereich, übergibt einen geprüften Kontext (nur vom Rahmen erzeugbar, ohne Adapter), sammelt Änderungen und Ereignisse, schreibt Verlauf und Ereignisse und committet.
3. **Vorschau per Probelauf (T3-B):** Die Operation läuft vollständig in der Transaktion, der Rahmen bildet die Vorschau aus den gesammelten Änderungen und rollt zurück. Jede schreibende Operation hat damit eine Vorschau ohne eigenen Vorschaucode.
4. **Freigabe-Beleg im Server (T4-B):** Die Vorschau speichert Person, Aufruf(e), Parameter und eine Prüfsumme der Änderungen mit Ablaufzeit und gibt eine Beleg-ID zurück. Aufrufe des Assistenten werden nur mit gültigem Beleg ausgeführt; weichen die Änderungen beim Ausführen ab, ist eine neue Freigabe nötig. Direkte Aufrufe aus der Oberfläche bleiben einstufig.
5. **Stapel (T5-B):** Der Assistent kann eine Folge von Aufrufen vorschlagen; Vorschau, Freigabe und Ausführung gelten für den ganzen Stapel, in einer Transaktion mit einer Bündel-ID (alles oder nichts), mit Obergrenze.
6. **Transport (T6-A):** RPC, `POST /api/v1/operations/{name}`, Stapel über einen eigenen Endpunkt.
7. **Festlegungen:** Akteur-Arten Person, Assistent im Auftrag von Person, Regel, Gast, Import; Fehler als Codes mit Parametern, Texte erst im Client bzw. in der Antwort des Assistenten; Namen `bereich.verb`, fachliche statt technischer Operationen.

Gründe: V2 erfüllt Vorschaupflicht, Freigabe, Berechtigung an einer Stelle, Verlauf und Ereignisbildung **durch Konstruktion** statt durch Sorgfalt je Operation. Für eine Person mit Agenten ([RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)) ist das der größte Hebel; der Mehraufwand fällt einmal im Rahmen an. V3 lohnt nur bei einem realistischen Sprachwechsel; der Rahmen kapselt die Schemaquelle, ein späterer Übergang bleibt möglich.

## Folgen
- **Leichter:** Neue Operation = Fachlogik plus Geltungsbereich (Änderbarkeit, R-A2 sinkt); Agenten können den Querschnitt nicht vergessen; Verlauf mit Akteur und Bündel und die serverseitige Freigabe stützen Nachvollziehbarkeit und RA-010; „lesend“ wird von PostgreSQL erzwungen.
- **Schwerer:** Rahmencode als Eigenbau; der Geltungsbereich muss sich aus den Parametern ableiten lassen (Sonderfälle Gast, Feed, Import brauchen eigene Bereichsarten); Operationen dürfen keine Wirkung außerhalb der Datenbank haben (Adapter nur über Outbox und Kostenerfassung); Vorschauen halten kurz Sperren; die Vorschau ist generisch formuliert (aus Änderungen), nicht frei je Operation.
- **Risiken (Kapitel 11):** R-A2 erhält die Maßnahme „Rahmen nach ADR-005“. Neu zu beobachten: Sperrdauer des Probelaufs bei großen Stapeln.
- **Bindet oder gibt frei:** E-009 (KI-Anbindung) ist frei: Werkzeugschemas, Freigabe-Beleg und Stapel stehen fest. E-016 (Architekturtests) erhält eine Regel mehr: Fachbereiche erreichen Adapter nicht. E-008 (Gast) muss sich in die Akteur- und Bereichsarten einfügen. E-017 (Import) nutzt die Akteur-Art Import.

## Noch festzulegen (ohne neue Entscheidung)
1. **Spike-Erweiterung E-005a:** Rahmen für `appointment.create`, `appointment.cancel`, `appointment.reschedule` und einen Stapel; `schemars` gegen utoipa; messen: Zeilen je Operation, Zeilen des Rahmens, Dauer und Sperren des Probelaufs unter Last (M-4), ob ein Agent eine neue Operation ohne Kenntnis des Querschnitts richtig anlegt.
2. **Werte:** Obergrenze für Stapel (Vorschlag 50 Aufrufe oder 500 betroffene Objekte), Ablaufzeit des Freigabe-Belegs (Vorschlag 10 min).
3. **Sprache der Operationsbeschreibungen für die KI** (Deutsch oder Englisch); die Antwortsprache der Person bleibt unberührt.
4. **Folgeänderungen in arc42:** K-002 (Geltungsbereich als Ort der Prüfung), K-004 (Akteur-Arten, Bündel aus Stapel), Kapitel 5 Ebene 2 (Rahmen als Baustein), Kapitel 11 R-A2.

## Wann überprüfen?
- Wenn E-005a zeigt, dass der Probelauf unter Last zu lange sperrt: auf Planen und Anwenden (T3-C) wechseln, die Operationen werden dabei nur aufgeteilt.
- Wenn Operationen Wirkungen außerhalb der Datenbank brauchen, die sich nicht über die Outbox abbilden lassen.
- Wenn eine öffentliche API für Dritte gefordert wird (dann REST-Abbildung, T6-B).
- Wenn ein Sprachwechsel realistisch wird (dann V3).
