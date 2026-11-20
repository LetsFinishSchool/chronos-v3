---
id: F-015
title: KI-Assistent
status: entwurf
typ: feature
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-008, SH-002]
---

# F-015: KI-Assistent

**Story:** Als Leitungsteam-Mitglied möchte ich komplexe Aufgaben einem KI-Assistenten im Dialog geben, damit ich sie nicht mühsam in der Oberfläche zusammenklicke.

**Umfang:**
- Dialog-Assistent neben der Weboberfläche
- Alle Funktionen von Chronos sind über den Assistenten aufrufbar
- Typische Aufgaben: Serientermin mit komplexer Regel, komplexe Team-Struktur, Bulk-Aktionen
- Vorschau und Freigabe vor jeder Schreiboperation
- Kostenerfassung der KI-Nutzung

**Entscheidung:**
- Anbieterneutrale Schnittstelle, Start mit Claude; konkretes Modell in arc42.
- Monatslimit je Team, der Betreiber trägt die Kosten ([F-018](F-018-kostenerfassung.md)).

**Offen:**
- Datenschutz beim KI-Anbieter im Detail (AV-Vertrag, Datenumfang)
- Wie Gäste ohne Konto den Assistenten nutzen: nicht (?)

**Anforderung mit Akzeptanzkriterien:** [FA-015](../anforderungen/FA-015-ki-assistent.md)
