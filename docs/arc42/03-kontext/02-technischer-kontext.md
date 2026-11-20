---
title: Technischer Kontext
status: entwurf
quellen: [req42 SC-001, RB-002, FA-009, FA-014, QA-006]
---

# 3.2 Technischer Kontext

Aufgeführt sind nur Schnittstellen, deren Art durch Standards oder req42 feststeht. Was offen ist, steht in der Spalte „Offen“ und verweist auf [Kapitel 9](../09-entscheidungen/01-offene-entscheidungen.md).

| Nachbar | Technische Schnittstelle (festgelegt) | Offen |
|---|---|---|
| Browser der Nutzer | HTTPS; mobil-zuerst Web-Oberfläche | Frontend-Technik (E-004) |
| Keycloak | Anmeldung über den geteilten Dienst, keine Passwörter in Chronos | Protokoll, Sitzungs- und Gastkonzept (E-008) |
| Push-Dienste | Web Push (Standard), verschlüsselte Nutzlast | Bibliothek, Abo-Verwaltung (E-006) |
| Mailserver | SMTP-Relay oder EU-Anbieter | Anbieter (E-011) |
| Messenger | optional (Telegram, WhatsApp), hinter einer Kanal-Abstraktion | Auswahl später |
| KI-Anbieter | Anbieterneutral, Start mit Claude; Monatslimit je Team | Abstraktion, Datenschutz im Detail (E-009) |
| Ferien-API | Öffentliche API, Antworten werden zwischengespeichert | Anbieter der Daten |
| Kalender-Apps | `webcal`-URL mit nicht erratbarem, erneuerbarem Token; iCalendar (RFC 5545) | – |
| Backup-Speicher | S3-kompatibler EU-Objektspeicher, tägliche, clientseitig verschlüsselte Sicherung | Anbieter, Schlüsselverwaltung (E-010) |
| Beobachtung | Metriken und Logs mit durchgängiger Korrelations-ID | Werkzeuge im Budget (E-012) |
| chronos-root | Lesender Zugriff auf Altdaten; Übernahme wiederholbar, ohne Datenverlust im Altsystem | Zugriffsweg, Altschema prüfen (E-017) |
| Betreiber (Konfiguration) | Konfiguration und Secrets von außen, nie im Repository | Mechanismus |

## Zusätzliche Eingänge

- **Zeitgesteuerte Auslöser** (Erinnerungen, wöchentliche Zusammenfassung, Fristen, Ablauf von Links, 30-Tage-Löschung): Chronos handelt auch ohne Benutzeraktion ([FA-005](../../req42/04-product-backlog/anforderungen/FA-005-rueckmeldung.md), [FA-017](../../req42/04-product-backlog/anforderungen/FA-017-rueckgaengig-machen.md)). Der Mechanismus ist offen (E-006).
- **Operationsaufrufe des Assistenten** kommen über dieselbe Schicht wie die der Oberfläche ([K-006](../08-konzepte/K-006-operationsschicht-und-assistent.md)).
