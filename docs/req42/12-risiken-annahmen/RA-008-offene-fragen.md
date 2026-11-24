---
id: RA-008
title: Offene Fragen an den Product Owner
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: annahme
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [SH-001]
---

# RA-008: Offene Fragen an den Product Owner

Alles mit **(?)** in req42 ist vorläufig. Bündelung:

**Entschieden am 2026-11-20 (Entwurf):** Mitgliedschaft erbt nach oben, Gäste nicht; jedes Mitglied darf entfernen/löschen, mit Änderungsverlauf; Mindestteilnehmerzahl entfällt; Veranstaltung ist nur interne Klammer.

**Entschieden (Runde 5):** Mehrsprachigkeit Deutsch/Englisch; PR-Regeln sind keine Randbedingung (RB-007 entfallen); alles ist rückgängig machbar; Kosten je Benutzer/Team mit Einzelposten; Serientermine mit vollem RRULE und Schulferien-Ausnahmen; KI-Assistent mit Freigabe vor Schreiben; dauerhafte Zeitraumsregeln; schlanke Web-UI.

**Entschieden (Runde 6, 2026-11-20):** Team löschen = Kaskade mit Rückgängig; Zeitzone je Team/Termin (Standard Europe/Berlin); gelöschte Objekte 30 Tage wiederherstellbar; Antwortskala Ja/Vielleicht/Nein; Korrekturnachricht bei Rücknahme; Linkarten Team-Einladung und Termin-Gastlink, Gastlink bis Terminende + 30 Tage; Gast kann Handeln ins Konto übernehmen; KI anbieterneutral, Start mit Claude, Monatslimit je Team, Betreiber trägt Kosten; Gastsprache Browsersprache (Rückfall Deutsch); Erinnerungszeitpunkte stellt der Benutzer ein (je Termin überschreibbar über den Assistenten); Schulferien per öffentlicher API mit Cache; Mailversand per SMTP-Relay/EU-Anbieter; Datenbank wird in arc42 entschieden; Umgebungen prod und staging im geteilten Cluster; vorhandenes Keycloak; Product Owner ist Datenschutzverantwortlicher, Standardtexte DE/EN; RPO 24 h, RTO 8 h, Seite < 1 s, Zustellquote > 95 %; Roadmap nach Wert (Kern zuerst, Migration vor Prod-Umstellung). Vorschlag: `wiki/proposals/2026-11-20-ra-008-offene-fragen-runde-6.md`.

**Entschieden (Runde 7):** Neue Ziele [Z-009](../01-ziele/Z-009-benachrichtigungen-sparsam-halten.md) (max. 2 × Termine der Woche an Benachrichtigungen, alle Push/Mail zählen, nur Planung ohne Laufzeitsperre, überschreibbar) und [Z-010](../01-ziele/Z-010-rueckmeldungen-automatisch-einholen.md) (Rückmeldungen automatisch einholen: Erinnerung 1 Woche und 3 Tage vorher, wöchentliche Zusammenfassung der nächsten 14 Tage, Leitung wird bei Ausbleiben informiert).

**Entschieden (Runde 8):** Leitung wird einmalig 2 Tage vor dem Termin über ausbleibende Rückmeldungen informiert; Backup-Ziel ist ein S3-kompatibler EU-Objektspeicher, clientseitig verschlüsselt.

**Entschieden (Runde 9):** Mindestbreite 320 px, mobil zuerst; Antwortquote ≥ 80 % (48 h vor Beginn).

**Entschieden (Runde 10):** Zeitplan als Meilensteine ohne feste Termine; Betrieb im bestehenden Cluster-Budget mit geringen Zusatzkosten; keine benannte Vertretung (nur Dokumentation, akzeptiertes Restrisiko, siehe RA-003).

**Entschieden (Runde 11):** Obergrenze 10 € pro Monat für Zusatzkosten; bei Erreichen pausiert die KI, der Betreiber wird benachrichtigt.

**Noch offen:**

| Bereich | Offene Frage |
|---|---|
| KI und Kosten | Datenschutz beim KI-Anbieter im Detail |
| Kanäle | Messenger-Auswahl später |
| Betrieb | Backup-Anbieter und Schlüsselverwaltung (Ziel: S3-kompatibler EU-Objektspeicher) |
