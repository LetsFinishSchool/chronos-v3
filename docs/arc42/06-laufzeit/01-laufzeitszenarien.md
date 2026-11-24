---
title: Laufzeitszenarien
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 FA-002, FA-005, FA-008, FA-015, FA-016, FA-017, FA-012, M-004]
---

# Kapitel 6: Laufzeitsicht

Die Szenarien zeigen das **geforderte Verhalten** zwischen den [Bausteinen](../05-bausteine/01-bausteinsicht.md) (Kandidaten). Technische Mechanismen (Outbox, Worker, Transaktionsgrenzen, siehe [ADR-005](../09-entscheidungen/ADR-005-operationsschicht.md)) sind hier abstrakt als „festhalten“ bzw. „Zeitauslöser“ bezeichnet.

## L-1 Antwort über Gastlink

```mermaid
sequenceDiagram
  actor G as Gast
  participant UI as Weboberfläche
  participant OP as Operationsschicht
  participant BE as Berechtigung und Zugang
  participant RM as Rückmeldung
  participant EV as Ereignisse
  G->>UI: Link öffnen, Namen angeben, antworten
  UI->>OP: Antwort setzen (Token, Name, Antwort)
  OP->>BE: Token prüfen (gültig, nicht widerrufen, nicht abgelaufen)
  BE-->>OP: Gast-Person für diesen Termin
  OP->>RM: Rückmeldung speichern
  RM->>EV: Ereignis "Rückmeldung geändert"
  OP-->>UI: bestätigt
```
Antwort in ≤ 3 Interaktionen ([QA-005](../../req42/06-qualitaet/QA-005-bedienbarkeit-mobil.md)). Ein widerrufener oder abgelaufener Link liefert keine Daten.

## L-2 Termin ändern und Benachrichtigung zustellen

```mermaid
sequenceDiagram
  actor M as Mitglied
  participant OP as Operationsschicht
  participant TE as Termine
  participant VL as Änderungsverlauf
  participant EV as Ereignisse
  participant NB as Benachrichtigung
  participant KA as Kanal Push
  participant KM as Kanal E-Mail
  participant KO as Kostenerfassung
  M->>OP: Termin verschieben
  OP->>TE: ändern
  TE->>VL: Eintrag mit Akteur, Vorher-Zustand
  TE->>EV: Ereignis "Termin geändert", Auslöser Mitglied, Korrelations-ID
  EV->>NB: festhalten, Empfänger bestimmen (Antwort ≠ abgesagt)
  NB->>KA: zustellen (höchstens einmal je Empfänger und Kanal)
  KA--xNB: fehlgeschlagen
  NB->>KM: Ersatzkanal, sofern erlaubt
  KM-->>NB: zugestellt
  NB->>KO: Kostenposten (E-Mail)
  NB->>NB: Protokoll: Auslöser, Empfänger, Kanal, Ergebnis
```
Das Ereignis wird vor der Zustellung dauerhaft festgehalten; ein Neustart während des Versands verliert nichts und stellt nichts doppelt zu ([QA-004](../../req42/06-qualitaet/QA-004-zuverlaessige-benachrichtigung.md)).

## L-3 Automatische Rückmelde-Erinnerung

```mermaid
sequenceDiagram
  participant ZT as Zeitauslöser
  participant RM as Rückmeldung
  participant EV as Ereignisse
  participant NB as Benachrichtigung
  ZT->>RM: Termine in 7 Tagen / 3 Tagen / 2 Tagen mit offenen Rückmeldungen
  RM->>EV: Ereignis "Erinnerung" je betroffener Person; "Ausbleibend" an Leitung (einmalig, 2 Tage)
  EV->>NB: Empfänger je Person, Erinnerungen bündeln
  NB->>NB: Benachrichtigungsbudget der Person beachten (Planung, keine Sperre)
```
Zusätzlich einmal pro Woche eine Zusammenfassung der offenen Rückmeldungen der nächsten 14 Tage. Die Leitung muss nichts auslösen ([Z-010](../../req42/01-ziele/Z-010-rueckmeldungen-automatisch-einholen.md)).

## L-4 Assistent: Vorschau und Freigabe

```mermaid
sequenceDiagram
  actor M as Mitglied
  participant AS as Assistent
  participant KI as KI-Anbieter
  participant KO as Kostenerfassung
  participant OP as Operationsschicht
  M->>AS: "Sage alle Termine in den Herbstferien ab"
  AS->>KO: Limit prüfen
  AS->>KI: Dialog
  KO-->>KO: Kostenposten (auch bei Fehlversuch)
  KI-->>AS: geplante Operation
  AS->>OP: Vorschau anfordern (lesend)
  OP-->>AS: betroffene Objekte, Änderungen, Anzahl
  AS->>M: Vorschau anzeigen
  M->>AS: Freigabe
  AS->>OP: Operation ausführen (mit Rechten der Person, Bündel-ID)
  OP-->>AS: Ergebnis, im Verlauf "durch Assistent im Auftrag von …"
```
Ohne Freigabe wird nichts geschrieben. Lesende Operationen brauchen keine Freigabe ([FA-015](https://github.com/LetsFinishSchool/chronos-v3/issues/80)). Ist das Monatslimit erreicht, pausiert die KI bis Monatsende.

## L-5 Zeitraumsregel wirkt auf bestehende und künftige Termine

1. Regel anlegen (nach Vorschau und Freigabe über den Assistenten): alle Termine im Zeitraum werden abgesagt, als **ein Bündel**, mit **einer** gebündelten Benachrichtigung je Empfänger.
2. Später wird im Zeitraum ein Termin angelegt: Er wird automatisch abgesagt; die anlegende Person erhält einen Hinweis, welche Regel gewirkt hat.
3. Regel aufheben: durch sie abgesagte Termine werden wieder geplant; manuell abgesagte bleiben abgesagt (Herkunft der Absage muss erkennbar sein).

## L-6 Gelöschtes wiederherstellen

```mermaid
sequenceDiagram
  actor M as Mitglied
  participant OP as Operationsschicht
  participant VL as Änderungsverlauf
  participant EV as Ereignisse
  M->>OP: gelöschtes Team/Termin oder Bündel wiederherstellen
  OP->>OP: Frist (30 Tage) prüfen, Objekt samt Inhalten wiederherstellen
  OP->>VL: Wiederherstellung protokollieren
  OP->>EV: "Wiederhergestellt", Korrekturnachricht an zuvor Informierte
```
Nach 30 Tagen wird endgültig gelöscht ([K-008](../08-konzepte/K-008-sicherheit-und-datenschutz.md)).

## L-7 Datenübernahme

Ablauf: Altdaten lesen → Abbildung nach [M-005](../../req42/05-modelle/M-005-migrationsabbildung.md) → schreiben → **Abgleich der Datensatzzahlen je Entität** mit dokumentierten Abweichungen. Wiederholbar, Altsystem bleibt unverändert, bestehende Keycloak-Kennungen bleiben gültig ([FA-012](https://github.com/LetsFinishSchool/chronos-v3/issues/1)). Die Übernahme löst keine Benachrichtigungen aus (zu entscheiden in E-017).
