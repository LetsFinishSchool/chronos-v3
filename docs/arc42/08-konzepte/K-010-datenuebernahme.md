---
title: K-010 Datenübernahme
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 RB-004, FA-012, M-005, RA-005, RM-001]
---

# K-010: Datenübernahme aus chronos-root

**Vorgaben** ([FA-012](../../req42/04-product-backlog/anforderungen/FA-012-datenuebernahme.md), [M-005](../../req42/05-modelle/M-005-migrationsabbildung.md)):

- Übernommen werden Benutzer (Keycloak-Kennung bleibt, Logins gültig), Termine mit Zu-/Absagen, Gruppen als Teams (flach, Besitzer wird Mitglied), Terminnachrichten. Freundschaften, Mindestteilnehmerzahl und abgeleiteter Status entfallen. Geräteabos optional.
- **Wiederholbar**, ohne Datenverlust im Altsystem.
- **Abgleich** der Datensatzzahlen je Entität, Soll 100 %, Abweichungen dokumentiert ([Z-006](../../req42/01-ziele/Z-006-bestandsdaten-verlustfrei-uebernehmen.md)).
- Migration vor Produktivschaltung, Meilenstein [RM-001](../../req42/11-roadmaps/RM-001-fundament-mit-datenuebernahme.md).
- Altschema ist gegen die Datenbank von chronos-root zu prüfen (offen in M-005); drei Abbildungen sind unsicher: Termin-Besitz je Team (**entschieden, PO 2026-11-20:** Termin wird je Team dupliziert; Folge: Dubletten, Rückmeldungen laufen je Kopie getrennt), Teilnahme-Rolle → Label (**entschieden, PO 2026-11-20:** Rollen werden verworfen), grobe Einstellungsabbildung (**entschieden, PO 2026-11-20:** Einstellungen werden verworfen, Neuschema-Standardwerte gelten; Benutzer setzen sie neu).
- Der Import ist vom laufenden Betrieb getrennt und darf nicht Teil des Dauerbetriebs-Budgets sein.

**Folge:** Der Import läuft durch dieselben Regeln wie normale Operationen, **ohne** Benachrichtigungen auszulösen und ohne Verlauf mit falschem Akteur (Ereignisse werden erzeugt, als „importiert“ markiert und nicht zugestellt, PO 2026-11-20; Verfahren entschieden, PO 2026-11-20: eigenes Import-Werkzeug über die Operationsschicht mit Importmodus; siehe [E-017](../09-entscheidungen/01-offene-entscheidungen.md)).
