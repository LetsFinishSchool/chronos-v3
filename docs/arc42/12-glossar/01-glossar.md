---
title: Glossar (Architektur)
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 08-terminologie/glossar.md]
---

# Kapitel 12: Glossar

Die **Fachbegriffe** stehen maßgeblich im [req42-Glossar](../../req42/08-terminologie/glossar.md) und werden hier nicht wiederholt. Ergänzt sind Begriffe, die die Architektur einführt.

| Begriff | Bedeutung |
|---|---|
| Operationsschicht | Vollständige Menge benannter Fachoperationen; einziger Weg für Zustandsänderungen und Abfragen. Oberfläche und Assistent nutzen sie gleichrangig ([K-006](../08-konzepte/K-006-operationsschicht-und-assistent.md)). |
| Operation | Eine benannte, beschriebene Fachfunktion (lesend oder schreibend), mit Berechtigung, Verlauf und ggf. Vorschau. |
| Vorschau | Wirkungsfreie Darstellung dessen, was eine schreibende Operation täte (Objekte, Änderungen, Anzahl). |
| Ereignis | Fachliches Vorkommnis mit benanntem Auslöser, dauerhaft festgehalten. Nicht zu verwechseln mit der *Veranstaltung* (Code-Namenskonflikt, [E-015](../09-entscheidungen/01-offene-entscheidungen.md)). |
| Auslöser | Person, Assistent im Auftrag einer Person, Regel oder Zeitauslöser, der ein Ereignis verursacht. |
| Zeitauslöser | Zeitgesteuerter Auslöser ohne Benutzeraktion (Erinnerung, Frist, Ablauf, Löschung nach 30 Tagen). |
| Bündel | Zusammengehörige Änderungen (Bulk, Assistent, Regel) mit gemeinsamer Bündel-ID im Verlauf; gebündelte Löschungen sind als Ganzes wiederherstellbar. |
| Änderungsverlauf | Protokoll aller Änderungen mit Akteur, Aktion, Vorher-Zustand, Zeitpunkt und Bündel-ID. |
| Korrelations-ID | Kennung, die eine Anfrage oder einen Zeitauslöser durch Operation, Ereignis, Zustellung und Kostenposten verfolgt. |
| Kanal-Abstraktion | Einheitliche Schnittstelle der Zustellkanäle (Push, E-Mail, Messenger); neue Kanäle ohne Änderung der Ereignislogik. |
| Benachrichtigungsbudget | Standardgrenze von 2 × Termine der Woche je Person; wird geplant, nicht erzwungen. |
| Adapter | Baustein, der genau einen Nachbarn (Keycloak, Mailserver, KI-Anbieter, …) kapselt. |
| Gast-Person | Person ohne Konto, die über einen Termin-Gastlink antwortet. |
| Änderungsachse | Erwartete Richtung künftiger Änderungen mit Soll-Eigenschaft ([Veränderlichkeit](../04-loesungsstrategie/02-veraenderlichkeit.md)). |
