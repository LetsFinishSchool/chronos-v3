---
id: ADR-002
title: Zerlegung: Monolith plus Worker
status: angenommen
freigegeben-am: 2026-11-20
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-001]
quellen: [Gespräch mit dem Product Owner 2026-11-20, ADR-001]
---

# ADR-002: Zerlegung: Monolith plus Worker

## Kontext
Treiber: Atomarität von Zustandsänderung, Verlauf und Ereignis ([K-003](../08-konzepte/K-003-ereignisse-und-benachrichtigung.md), [K-004](../08-konzepte/K-004-aenderungsverlauf-und-rueckgaengig.md)); Budget 1 vCPU / 1 GiB ([RB-003](../../req42/07-randbedingungen/RB-003-ressourcenbudget.md)); Änderbarkeit auf Platz 1 ([ADR-001](ADR-001-prioritaet-der-qualitaetsziele.md)); Ein-Personen-Betrieb ([RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)).

## Optionen
A modularer Monolith (ein Prozess); **B Monolith plus Worker**; C mehrere Dienste. A hatte die geringste Grundlast, C verteilt die Konsistenz von Verlauf und Wiederherstellung und wurde als zu aufwendig eingeschätzt.

## Entscheidung
**B: Eine Codebasis mit einer gemeinsamen Operationsschicht und einer gemeinsamen Datenbank, betrieben als zwei Prozesse:**

- **Web:** beantwortet Anfragen von Oberfläche, Assistent-Clients und Feed.
- **Worker:** führt Hintergrundverarbeitung aus, mindestens **Zeitauslöser** (Erinnerungen, Zusammenfassungen, Fristen, Linkablauf, endgültiges Löschen nach 30 Tagen) und **Zustellung** der Benachrichtigungen samt Wiederholung. Ob KI-Aufrufe, Backup und Import hier oder im Web laufen, entscheiden E-009, E-010 und E-017.

Beide Prozesse nutzen dieselben Fachbereiche, dieselben Regeln und dieselbe Datenbank. Der Austausch läuft über die Datenbank (festgehaltene Ereignisse und Aufträge), nicht über direkte Aufrufe; der genaue Mechanismus ist E-006.

## Folgen
- **Budget:** Das Gesamtbudget wird auf zwei Prozesse verteilt, die Grundlast fällt doppelt an. Das macht eine Laufzeit mit geringem Grundspeicher in E-002 noch wichtiger.
- **Atomarität bleibt:** Zustandsänderung, Verlauf und Ereignis entstehen in einer Transaktion der Web-Seite; der Worker verarbeitet danach.
- **Entkopplung:** Zustellungsfehler, Wiederholungen und Zeitauslöser belasten das Web nicht; ein Neustart des Web verliert keine Zustellungen (QA-004).
- **Modulgrenzen** bleiben innerhalb der Codebasis und werden durch Architekturtests geprüft (E-016); die Prozessgrenze ersetzt sie nicht.
- **Deployment:** zwei Container (Web, Worker) aus **einem** Image, das Binary `chronos` wählt per Unterbefehl den Prozess (PO 2026-11-24; ersetzt „zwei Container mit je eigenem Image“ vom 2026-11-20), je Umgebung prod und staging.
- **Konsequenz für E-003:** Die Datenbank muss gleichzeitigen Zugriff von zwei Prozessen vertragen (schränkt z. B. dateibasierte Datenbanken ein).
- **Konsequenz für E-006:** Der Mechanismus „Ereignis festhalten, Worker arbeitet ab“ ist jetzt Pflicht, nicht mehr optional.

## Wann überprüfen?
Wenn das gemessene Budget die doppelte Grundlast nicht trägt (dann zurück zu A mit Hintergrundverarbeitung im selben Prozess), oder wenn weitere Hintergrundlast (z. B. KI) eine feinere Trennung verlangt.
