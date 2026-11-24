---
title: Technischer Kontext
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [req42 SC-001, RB-002, FA-009, FA-014, QA-006]
---

# 3.2 Technischer Kontext

Aufgeführt sind nur Schnittstellen, deren Art durch Standards oder req42 feststeht. Was offen ist, steht in der Spalte „Offen“ und verweist auf [Kapitel 9](../09-entscheidungen/01-offene-entscheidungen.md).

| Nachbar | Technische Schnittstelle (festgelegt) | Offen |
|---|---|---|
| Browser der Nutzer | HTTPS; mobil-zuerst Web-Oberfläche | – ([ADR-007](../09-entscheidungen/ADR-007-frontend-spa-svelte.md): SPA/PWA mit Svelte 5) |
| Keycloak | Anmeldung über den geteilten Dienst, keine Passwörter in Chronos | – ([ADR-008](../09-entscheidungen/ADR-008-sitzung-und-gast-identitaet.md): BFF-Sitzung, Gast per Cookie und Rückkehr-Link) |
| Push-Dienste | Web Push (Standard), verschlüsselte Nutzlast | – (`web-push-native`, [ADR-004](../09-entscheidungen/ADR-004-sprache-und-laufzeit.md); Abo-Lebenszyklus in ADR-008) |
| Mailserver | SMTP-Relay oder EU-Anbieter | – (E-011: generisches SMTP, Anbieter per Konfiguration) |
| Messenger | optional (Telegram, WhatsApp), hinter einer Kanal-Abstraktion | Auswahl später |
| KI-Gateway (LiteLLM, vom Betreiber) | OpenAI-kompatibles `/chat/completions` mit festem Modellnamen je Umgebung und virtuellem Schlüssel; Kosten je Aufruf und genutztes Modell in Antwort-Kopfzeilen ([ADR-006](../09-entscheidungen/ADR-006-ki-anbindung.md)) | Ort und Version des Gateways |
| KI-Anbieter | Nur über das Gateway; nur Anbieter mit garantiertem EU-Datenstandort (ADR-006); Monatslimit je Team | Standardmodell nach Prüfkatalog |
| Ferien-API | Öffentliche API, Antworten werden zwischengespeichert | Anbieter der Daten |
| Kalender-Apps | `webcal`-URL mit nicht erratbarem, erneuerbarem Token; iCalendar (RFC 5545) | – |
| Backup-Speicher | S3-kompatibler EU-Objektspeicher, tägliche, clientseitig verschlüsselte Sicherung | – (E-010: Anbieter nach Preis und EU-Standort austauschbar, Schlüssel beim Betreiber) |
| Beobachtung | Metriken und Logs mit durchgängiger Korrelations-ID | – (E-012: Bestand im Cluster) |
| chronos-root | Lesender Zugriff auf Altdaten; Übernahme wiederholbar, ohne Datenverlust im Altsystem | Zugriffsweg, Altschema prüfen (E-017) |
| Betreiber (Konfiguration) | Konfiguration und Secrets von außen, nie im Repository | Mechanismus |

## Zusätzliche Eingänge

- **Zeitgesteuerte Auslöser** (Erinnerungen, wöchentliche Zusammenfassung, Fristen, Ablauf von Links, 30-Tage-Löschung): Chronos handelt auch ohne Benutzeraktion ([FA-005](https://github.com/LetsFinishSchool/chronos-v3/issues/17), [FA-017](https://github.com/LetsFinishSchool/chronos-v3/issues/32)). Der Mechanismus: Ereignisse in der Datenbank festhalten, Worker arbeitet ab (E-006).
- **Operationsaufrufe des Assistenten** kommen über dieselbe Schicht wie die der Oberfläche ([K-006](../08-konzepte/K-006-operationsschicht-und-assistent.md)).
