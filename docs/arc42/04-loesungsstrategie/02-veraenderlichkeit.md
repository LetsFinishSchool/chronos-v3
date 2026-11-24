---
title: Veränderlichkeit und Erweiterungspunkte
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 QA-003, RM-006, RA-001, RB-001, F-008, F-014, F-015]
---

# Veränderlichkeit und Erweiterungspunkte

Das Projekt ist agil: Anforderungen kommen und gehen. Statt Zukünftiges zu raten, benennt diese Seite die **Änderungsachsen**, die req42 bereits erkennen lässt, und was die Architektur dafür **mindestens** leisten muss. Die Liste ist Arbeitsgrundlage und wird bei jeder neuen Anforderung geprüft: Passt sie in eine bekannte Achse, ist die Änderung billig; wenn nicht, ist das ein Signal für eine Architekturanpassung.

| Achse | Heute bekannt | Soll-Eigenschaft |
|---|---|---|
| **Benachrichtigungskanäle** | Web Push, E-Mail; optional Telegram, WhatsApp ([RM-006](../../req42/11-roadmaps/RM-006-messenger-kanaele.md)) | Neuer Kanal ohne Änderung der Ereignislogik ([QA-003 a](../../req42/06-qualitaet/QA-003-aenderbarkeit.md)); Kosten- und Protokollpflicht gelten automatisch. |
| **Terminarten** | Treffen, Frist/Marke | Neue Art ohne Eingriff in Rückmeldung und Benachrichtigung ([QA-003 b](../../req42/06-qualitaet/QA-003-aenderbarkeit.md)). |
| **Fachfunktionen** | F-001..F-018 | Neue Funktion ist automatisch für den Assistenten aufrufbar ([QA-003 c](../../req42/06-qualitaet/QA-003-aenderbarkeit.md)), berechtigt, im Verlauf; Gelöschtes ist wiederherstellbar. |
| **Ereignisarten** | Matrix [M-004](../../req42/05-modelle/M-004-benachrichtigungsmatrix.md) | Neue Ereignisart = neue Zeile (Auslöser, Empfänger, Kanalwahl), kein Umbau. |
| **Sprachen** | DE, EN | Weitere Sprache ohne Umbau ([RB-001](../../req42/07-randbedingungen/RB-001-mehrsprachigkeit.md)). |
| **KI-Anbieter** | EU-Anbieter über KI-Gateway, anbieterneutral ([ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md)) | Anbieter- und Modellwechsel als Gateway-Konfiguration, ohne Änderung an Chronos. |
| **Identität** | Keycloak | Gäste und Konten teilen ein Personenkonzept; ein anderer Identitätsdienst berührt nur den Zugang. |
| **Berechtigungsmodell** | alle Mitglieder gleichberechtigt, Vererbung nach oben | Berechtigungsprüfung an einer Stelle; Rollen nachrüstbar, falls die Zielgruppe wächst ([RA-001](../../req42/12-risiken-annahmen/RA-001-zielgruppe-sind-leitungsteams.md)). |
| **Kalender-Ausgaben** | webcal-Feed | Weitere Ausgabeformate als Leser des Fachmodells. |
| **Datenquellen** | chronos-root (einmalig) | Import-Pfad vom Betrieb getrennt, wiederholbar. |
| **Entfallende Funktionen** | z. B. Mindestteilnehmerzahl, Freundschaften | Funktion lässt sich entfernen, ohne andere Bereiche anzufassen. |

## Prüffrage für jede neue oder geänderte Anforderung

1. Welche Achse? Gibt es keine, ist das eine neue Achse: hier ergänzen.
2. Wie viele Module berührt die Änderung? (Messgröße aus QA-003.)
3. Läuft sie durch die Operationsschicht, den Verlauf, die Kostenerfassung und die Ereignisbildung, ohne dass jemand daran denken muss?
