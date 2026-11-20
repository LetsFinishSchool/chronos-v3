---
title: Key Learnings aus chronos-root und Eckpunkte von chronos-v3
type: concept
sources:
  - session:2026-11-20 (Requirements-Engineering-Gespräch mit dem Product Owner)
  - docs/req42/
confidence: hoch
last-verified: 2026-11-20
---

# Key Learnings aus chronos-root und Eckpunkte von chronos-v3

Aussagen des Product Owners (verbindlich erst, wenn in `docs/req42/` freigegeben).

## Warum der Neuanfang
- Domänenmodell trägt nicht (Freunde/Gruppen/Rollen je Termin passen nicht zur Praxis).
- Onboarding/Zugang zu hoch (Keycloak-Registrierung nötig).
- Benachrichtigung unzuverlässig, Auslöser kaum nachvollziehbar.
- Codebasis schwer pflegbar: intransparenter Datenfluss, schlecht getrennt und abstrahiert, neue Features aufwendig.
- RAM-Verbrauch zu hoch für die verfügbaren Ressourcen.

## Eckpunkte
- Zielgruppe: ehrenamtliche **Leitungsteams** von Jugendverbänden. Kinder und Eltern sind explizit **keine** Zielgruppe.
- Keine Freundschaften. **Teams** mit beliebig tief verschachtelten **Unter-Teams**. Alle Mitglieder gleichberechtigt.
- **Labels** (frei, mehrfach) für Rolle/Aufgabe je Team, Unter-Team, Veranstaltung oder Termin; keine feste Rollenliste.
- **Veranstaltung** = öffentlich, vom Verband ausgerichtet. **Termin** = intern (z. B. Vorbereitungstreffen, Frist), optional einer Veranstaltung zugeordnet, nicht jeder Termin hat Zu-/Absage.
- Rückmeldung: Zusage / Absage / Zeitweise. Terminfindung per Abstimmung.
- Zugang: Einladungslink ohne Konto; Team-Beitritt per Link optional. Keycloak bleibt als geteilter Dienst.
- Kanäle: Web Push, E-Mail, Kalender-Feed (webcal); Messenger nur Option.
- Ressourcen: ~1 vCPU / 1 GB RAM (besser weniger) auf geteiltem k3s (3 Nodes); < 500 aktive Nutzer.
- Migration: Benutzer, Termine inkl. Zu-/Absagen, Gruppen -> Teams, Terminnachrichten. Geräteabos optional. Freundschaften entfallen.

## Entscheidungen Runde 4 (2026-11-20)
- Mitgliedschaft erbt **nach oben** (Unter-Team-Mitglied ist Mitglied der übergeordneten Teams); Gäste nur im konkreten Team.
- Jedes Mitglied darf Mitglieder entfernen/Teams löschen; dafür Änderungsverlauf und Benachrichtigung.
- Mindestteilnehmerzahl und abgeleiteter Terminstatus entfallen.
- Veranstaltung ist nur interne Klammer, keine öffentliche Seite, keine Teilnehmeranmeldung.
- Stand: `docs/req42/` neu geschrieben (Entwurf, alle `status: entwurf`), offene Punkte in `RA-008`.

## Entscheidungen Runde 5 (2026-11-20)
- Oberfläche und Benachrichtigungen mehrsprachig (Deutsch, Englisch zuerst); RB-001 ersetzt.
- PR-/Qualitätsregeln sind keine Randbedingung, werden in der Entwicklung festgelegt (RB-007 entfallen).
- Alle Änderungen rückgängig machbar, auch Löschen von Teams/Terminen.
- Kosten (WhatsApp, E-Mail, KI) je Benutzer, sonst Team, als rekonstruierbare Einzelposten (RB-010).
- Serientermine mit vollem RRULE plus Schulferien-Ausnahmen.
- KI-Assistent für komplexe Operationen und Bulk, Freigabe vor jeder Schreiboperation; alle Funktionen per Assistent aufrufbar, Web-UI bewusst einfach (RB-011); dauerhafte Zeitraumsregeln.
