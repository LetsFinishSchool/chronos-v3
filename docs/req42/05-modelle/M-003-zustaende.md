---
id: M-003
title: Zustände von Termin, Rückmeldung und Terminfindung
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: modell
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-003, F-005, F-006]
---

# M-003: Zustände von Termin, Rückmeldung und Terminfindung

```mermaid
stateDiagram-v2
  direction LR
  [*] --> geplant
  geplant --> abgesagt
  abgesagt --> geplant: wiederherstellen
  geplant --> geloescht
  geloescht --> geplant: wiederherstellen
  geplant --> vergangen: Ende erreicht
```

```mermaid
stateDiagram-v2
  [*] --> offen: eingeladen
  offen --> zugesagt
  offen --> abgesagt
  offen --> zeitweise
  zugesagt --> abgesagt
  zugesagt --> zeitweise
  abgesagt --> zugesagt
  abgesagt --> zeitweise
  zeitweise --> zugesagt
  zeitweise --> abgesagt
```

```mermaid
stateDiagram-v2
  [*] --> offen
  offen --> entschieden: Vorschlag festgelegt, Termin entsteht
  offen --> verworfen
```

- Nur die betroffene Person ändert ihre Rückmeldung, bis zum Terminbeginn; „offen“ kann nicht wieder gesetzt werden.
- Termine der Art Frist/Marke haben keine Rückmeldung.
- Es gibt keinen von der Teilnehmerzahl abgeleiteten Terminstatus (Mindestteilnehmerzahl entfällt, [F-003](../04-product-backlog/features/F-003-termine.md)).
