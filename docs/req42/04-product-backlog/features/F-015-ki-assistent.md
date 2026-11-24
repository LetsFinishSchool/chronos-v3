---
id: F-015
title: KI-Assistent
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
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
- Anbieterneutrale Schnittstelle über ein KI-Gateway; nur Anbieter mit garantiertem europäischem Datenstandort; konkretes Modell nach Prüfkatalog ([ADR-006](../../../arc42/09-entscheidungen/ADR-006-ki-anbindung.md)).
- Monatslimit je Team, der Betreiber trägt die Kosten ([F-018](F-018-kostenerfassung.md)).

**Offen:**
- AV-Vertrag und Aufbewahrung beim gewählten EU-Anbieter prüfen (ADR-006, Bedingung 7)
- Wie Gäste ohne Konto den Assistenten nutzen: nicht (?)

**Anforderung mit Akzeptanzkriterien:** [FA-015](../anforderungen/FA-015-ki-assistent.md)
