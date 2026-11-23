---
title: K-006 Operationsschicht und Assistent
status: entwurf
quellen: [req42 RB-011, FA-015, QA-003, RA-010, Z-008]
---

# K-006: Operationsschicht und Assistent

**Vorgaben:**

- Alle Fachfunktionen liegen hinter einer **vollständigen, von der Oberfläche unabhängigen Operationsschicht**. Oberfläche und Assistent sind gleichrangige Clients ([RB-011](../../req42/07-randbedingungen/RB-011-einfache-weboberflaeche-vollstaendige-funktionen-ueber-assistent.md)).
- Die Weboberfläche bildet bewusst **nicht alle** Operationen ab; der Assistent kann **jede** ausführen.
- Eine neue Operation steht dem Assistenten **ohne Zusatzaufwand** zur Verfügung (QA-003 c). Das verlangt, dass jede Operation maschinenlesbar beschrieben ist (Name, Parameter, lesend/schreibend, Wirkung).
- **Lesend** ohne Freigabe; **schreibend** nur nach Vorschau (betroffene Objekte, Änderungen, Anzahl) und ausdrücklicher Freigabe ([FA-015](../../req42/04-product-backlog/anforderungen/FA-015-ki-assistent.md)). Daraus folgt: Jede schreibende Operation muss eine **Vorschau ohne Wirkung** liefern können.
- Rechte der angemeldeten Person; Verlauf „durch Assistent im Auftrag von …“; gelöschte Bündel wiederherstellbar ([K-004](K-004-aenderungsverlauf-und-rueckgaengig.md)).
- KI-Nutzung ist kostenerfasst und limitiert ([K-005](K-005-kostenerfassung.md)); Antwortsprache wie die Person.
- **Prompt-Injection:** Inhalte aus Terminbeschreibungen, Nachrichten und Gast-Namen sind nicht vertrauenswürdig und dürfen den Freigabezwang nicht umgehen ([RA-010](../../req42/12-risiken-annahmen/RA-010-ki-assistent-risiken.md)).
- **Anbieterneutral** über ein KI-Gateway; nur Anbieter mit garantiertem EU-Datenstandort ([ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md)). Der KI-Anbieter erhält personenbezogene Daten; **Entschieden (PO 2026-11-20):** Offenlegung in der Datenschutzerklärung, Daten werden unverändert gesendet.

**Entschieden (PO 2026-11-23):** Form der Schicht nach [ADR-005](../09-entscheidungen/ADR-005-operationsschicht.md): Ein Rahmen trägt Transaktion, Berechtigung, Verlauf und Ereignis; die Vorschau entsteht per Probelauf mit Rollback; Aufrufe des Assistenten brauchen einen Freigabe-Beleg im Server; Stapel laufen atomar mit einer Bündel-ID.

**Entschieden (PO 2026-11-23):** KI-Anbindung nach [ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md): Der Assistent ist ein eigener Baustein im Web-Prozess und Client der Operationsschicht. Die Schleife läuft im Server (lesende Aufrufe direkt, schreibende als Stapel mit Freigabe-Beleg). Das Gespräch wird 24 h gespeichert. Die Anbindung läuft über das KI-Gateway mit Kosten je Aufruf aus der Antwort.
