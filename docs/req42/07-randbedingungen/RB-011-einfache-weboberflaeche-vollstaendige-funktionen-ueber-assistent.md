---
id: RB-011
title: Einfache Weboberfläche, vollständige Funktionen über den Assistenten
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: randbedingung
kategorie: konzeptionell
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [F-015]
---

# RB-011: Einfache Weboberfläche, vollständige Funktionen über den Assistenten

Die Weboberfläche bleibt so einfach wie möglich und bildet bewusst nicht alle Funktionen ab. **Alle** Funktionen von Chronos müssen als Operationen für den KI-Assistenten aufrufbar sein ([F-015](https://github.com/LetsFinishSchool/chronos-v3/issues/80)). Folge für die Architektur: Fachfunktionen liegen hinter einer vollständigen, von der Oberfläche unabhängigen Operationsschicht, die Weboberfläche und Assistent gleichermaßen nutzen ([QA-003](../06-qualitaet/QA-003-aenderbarkeit.md)). Schreibende Operationen des Assistenten benötigen Vorschau und Freigabe.
