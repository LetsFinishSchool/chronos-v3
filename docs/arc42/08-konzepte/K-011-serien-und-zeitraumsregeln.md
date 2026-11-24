---
title: K-011 Serien und Zeitraumsregeln
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 FA-014, FA-016, F-014, F-016, M-001]
---

# K-011: Serien und Zeitraumsregeln

**Serien** ([FA-014](../../req42/04-product-backlog/anforderungen/FA-014-serientermine.md)):

- Jede gültige **RRULE nach RFC 5545**; ungültige werden mit Fehlermeldung abgelehnt.
- **Ausnahmen:** einzelne Vorkommen (absagen, verschieben) und **Schulferien-Zeiträume** je Team; Ferien kommen aus einer öffentlichen API mit Cache.
- **Rückmeldung je Vorkommen.** Änderungen „ab hier“ oder „ganze Serie“ benachrichtigen die Eingeladenen.
- Der Kalender-Feed enthält die Vorkommen.

**Zeitraumsregeln** ([FA-016](../../req42/04-product-backlog/anforderungen/FA-016-zeitraumsregeln.md)):

- Eine Regel wirkt auf **bestehende und künftig angelegte** Termine im Zeitraum (absagen).
- Wird sie aufgehoben, werden nur die **durch sie** abgesagten Termine wieder geplant: Die Absage muss ihre Ursache (Regel, manuell) kennen.
- Absagen durch Regeln lösen **gebündelte** Benachrichtigungen aus.

**Gemeinsame Folge:** Serien und Regeln erzeugen viele Änderungen auf einmal. Sie müssen als **Bündel** im Verlauf stehen ([K-004](K-004-aenderungsverlauf-und-rueckgaengig.md)) und das Benachrichtigungsbudget wahren ([K-003](K-003-ereignisse-und-benachrichtigung.md)).

**Entschieden (PO 2026-11-20):** Vorkommen werden materialisiert ([E-013](../09-entscheidungen/01-offene-entscheidungen.md)). **Offen:** Zeithorizont der Serien; Verhalten bei Ausfall der Ferien-API.
