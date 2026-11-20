---
title: K-002 Berechtigung und Zugang
status: entwurf
quellen: [req42 M-002, FA-001, FA-002, FA-011, QA-007, RA-004, RA-007]
---

# K-002: Berechtigung und Zugang

**Vorgaben** ([M-002](../../req42/05-modelle/M-002-berechtigungen.md)):

- Alle Mitglieder eines Teams sind gleichberechtigt; **Labels geben keine Rechte**.
- Mitgliedschaft erbt **nach oben**: Mitglied eines Unter-Teams ist Mitglied aller übergeordneten Teams. Gäste erben nicht, sie gelten nur für das konkrete Team bzw. den konkreten Termin.
- „Nur die Person selbst“ ändert: eigene Antwort, Einstellungen, Feed-Link.
- Der Assistent handelt ausschließlich mit den Rechten der angemeldeten Person ([FA-015](../../req42/04-product-backlog/anforderungen/FA-015-ki-assistent.md)).
- Der Missbrauchsschutz ist nicht Einschränkung, sondern Nachvollziehbarkeit: Verlauf, Benachrichtigung der Betroffenen, Wiederherstellung gelöschter Objekte ([K-004](K-004-aenderungsverlauf-und-rueckgaengig.md)).

**Zugangsarten:**

| Art | Wirkung | Eigenschaften |
|---|---|---|
| Konto über Keycloak | volle Funktion | keine Passwörter in Chronos; Sitzung läuft für aktive Personen nicht sichtbar ab |
| Team-Einladungslink | Beitritt, setzt Konto voraus | Token nicht erratbar, widerrufbar |
| Termin-Gastlink | Antwort ohne Konto | gilt bis Terminende + 30 Tage, widerrufbar; Gast sieht nur, wofür der Link gilt |
| Kalender-Feed-Token | Lesezugriff auf den persönlichen Feed | erneuerbar, alter Token sofort ungültig |

**Architekturfolge:** Die Berechtigungsprüfung liegt an **einer** Stelle in der Operationsschicht, damit UI und Assistent nicht unterschiedlich prüfen und ein späteres Rollenmodell nachrüstbar bleibt ([RA-001](../../req42/12-risiken-annahmen/RA-001-zielgruppe-sind-leitungsteams.md)). Zugangstoken sind für Skripte der Seite nicht lesbar; wie Link-Token abgelegt werden, ist offen ([QA-007](../../req42/06-qualitaet/QA-007-sicherheit-und-datenschutz.md)).

**Offen:** Einbindung Keycloak und Sitzungsmechanik, Gast-Identität über mehrere Geräte ([E-008](../09-entscheidungen/01-offene-entscheidungen.md)).
