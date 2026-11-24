---
title: K-002 Berechtigung und Zugang
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
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

**Architekturfolge:** Die Berechtigungsprüfung liegt an **einer** Stelle in der Operationsschicht, damit UI und Assistent nicht unterschiedlich prüfen und ein späteres Rollenmodell nachrüstbar bleibt ([RA-001](../../req42/12-risiken-annahmen/RA-001-zielgruppe-sind-leitungsteams.md)). Zugangstoken sind für Skripte der Seite nicht lesbar; Link-Token liegen im Fragment der Adresse und in der Datenbank nur als Hash ([ADR-007](../09-entscheidungen/ADR-007-frontend-spa-svelte.md), [ADR-008](../09-entscheidungen/ADR-008-sitzung-und-gast-identitaet.md)) ([QA-007](../../req42/06-qualitaet/QA-007-sicherheit-und-datenschutz.md)).

**Geltungsbereich als Ort der Prüfung ([ADR-005](../09-entscheidungen/ADR-005-operationsschicht.md)):** Jede Operation beschreibt ihren Geltungsbereich (Team, Termin, Person, Gastlink, Feed, Import), abgeleitet aus den Parametern. Der **Rahmen** der Operationsschicht prüft ihn vor der Fachlogik anhand der Akteur-Art (Person, Assistent im Auftrag von Person, Regel, Gast, Import) und reicht einen geprüften Kontext weiter, den nur der Rahmen erzeugen kann. Die Fachlogik prüft nicht selbst. Sonderfälle haben eigene Bereichsarten: der Gast gilt nur für seinen Gastlink (die Operation `guest.claim` überträgt sein Handeln bei der Registrierung auf das Konto), der Feed liest nur, der Import hat eine eigene Art.

**Entschieden (PO 2026-11-24, [ADR-008](../09-entscheidungen/ADR-008-sitzung-und-gast-identitaet.md), freigegeben):** Sitzung als BFF mit Refresh-Heartbeat (6 Stunden) und Back-Channel-Logout; Link-Token im Fragment der Adresse ([ADR-007](../09-entscheidungen/ADR-007-frontend-spa-svelte.md)). **Gast (PO 2026-11-24):** Cookie plus persönlicher Rückkehr-Link. Sitzungsdauern: 30 Tage Leerlauf, 180 Tage Höchstdauer in Keycloak, 7 Tage Leerlauf in Keycloak.
