---
title: Fluent-Prüfung (Pflegestand, DATETIME, Werkzeuge) für ADR-010
type: concept
sources:
  - docs/arc42/09-entscheidungen/ADR-010-uebersetzungen-fluent.md (Entwurf)
  - docs/arc42/08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md
  - crates.io-API (fluent-bundle, fluent, fluent-datetime, fluent-syntax, fluent-langneg, intl-memoizer, unic-langid, icu), abgerufen 2026-11-24
  - GitHub-API projectfluent/fluent-rs (Commits, Issue 181), projectfluent/fluent.js (Commits), abgerufen 2026-11-24
  - npm-Registry @fluent/bundle, abgerufen 2026-11-24
  - https://docs.weblate.org/en/latest/formats/fluent.html
confidence: mittel
last-verified: 2026-11-24
---

# Fluent-Prüfung für ADR-010

Auftrag: Erfüllt Fluent die Chronos-Anforderungen (Pflege der Bibliotheken, DATETIME)? Das löst die ▲-Punkte in ADR-010. Ergebnis: **ja, mit zwei bewusst zu akzeptierenden Einschränkungen** (Serverseite ohne eingebautes `DATETIME`, Server-Bibliotheken ohne 1.0).

## Pflegestand

| Baustein | Version | Letzte Veröffentlichung | Aktivität im Repo | Bewertung |
|---|---|---|---|---|
| `fluent-bundle` (Rust) | 0.16.0 | 2025-05-22 | Repo `projectfluent/fluent-rs` nicht archiviert, letzter Push 2026-09-27, nur Lint/Docs-Commits seit Mai 2025; 67 offene Issues | Stabil, aber ruhig: wenig Weiterentwicklung. Pre-1.0 |
| `fluent` (Umbrella) | 0.17.0 | 2025-05-23 | wie oben | wie oben |
| `fluent-syntax`, `intl-memoizer`, `unic-langid`, `fluent-langneg` | 0.12.0 / 0.5.3 / 0.9.6 / 0.14.2 | 2025-05 bis 2025-10 | | Je ~25–33 Mio. Downloads, breite Nutzung (Mozilla) |
| `@fluent/bundle` (npm) | 0.19.1 | 2025-04-02 | `projectfluent/fluent.js` nicht archiviert, Commits bis 2026-01 (Vitest-Umstieg, Whitespace-Fix, `Intl.Locale` in langneg), letzter Push 2026-05-22 | Aktiver als die Rust-Seite; Master hat unveröffentlichte Änderungen, teils breaking (`!`) |

Einordnung: Fluent wird von Mozilla (Firefox) produktiv genutzt; Downloadzahlen der Rust-Crates (~9,5 Mio. in 90 Tagen) sind hoch. Das Risiko ist nicht „aufgegeben“, sondern „langsame Pflege, kein 1.0“. Für Chronos (de/en, wenige Nachrichten) reicht ein stabiler Funktionsumfang; das Format selbst ist seit Fluent 1.0 stabil.

## DATETIME

- **Browser (`@fluent/bundle`):** `DATETIME` und `NUMBER` sind eingebaut (über `Intl`). Nach dem 0.19.1-Fix für `FluentDateTime`/`FluentNumber` funktioniert die Primitivkonvertierung.
- **Server (`fluent-bundle` 0.16):** **Kein eingebautes `DATETIME`.** Issue [fluent-rs#181](https://github.com/projectfluent/fluent-rs/issues/181) „Implement the DATETIME() builtin function“ ist seit 2020 offen (letzte Änderung 2025-09-18). `NUMBER` ist vorhanden. ADR-010 Punkt 3 (Server formatiert vor der Übergabe) stimmt also.
- **Alternative:** Crate `fluent-datetime` 0.2.0 (2026-02-21) registriert `DATETIME` per `bundle.add_datetime_support()` auf Basis von ICU4X 2 (`icu_datetime`, `icu_calendar`) und **`jiff`** (`jiff-icu`). Einschränkung: Einzelpflege (Repo `g2p/fluent-datetime`, nicht Teil von projectfluent), nur ~12 000 Downloads; Anbindung an `fluent-bundle` 0.16. Passt zur Zeitbibliothek-Option B/C (`jiff`) in e-002-folgeentscheidungen-rust, nicht zu `chrono-tz` (Spike).
- ICU4X selbst ist gepflegt (`icu` 2.4.0, 2026-10-22).

## Übersetzungswerkzeug

Weblate unterstützt `.ftl` (monolingual, Beschreibungen, Fluent-Syntaxprüfungen). **Nicht unterstützt:** Plural-Flags, Kontext, Ortsangaben. Plural/Auswahl stehen in Fluent in der Nachricht (Selektoren); Weblate behandelt solche Nachrichten als Ganzes. Für zwei Sprachen und eine Person als Übersetzer ausreichend; kein Weblate-Betrieb nötig, solange die Dateien im Repository gepflegt werden. Ungeprüft: Verhalten bei komplexen Selektoren in der Weblate-Oberfläche.

## Empfehlung (unverbindlich, Entscheidung beim PO)

1. Fluent bleibt tragfähig. Pflegestand-▲ in ADR-010 gilt als geprüft; Wiedervorlage-Kriterium („nicht mehr gepflegt“) beibehalten, Stichtag z. B. bei Umsetzungsbeginn (`fluent-bundle` ohne Release seit 2025-05).
2. Datum im Server wie in ADR-010 vor der Übergabe formatieren (kein Abhängigkeitsrisiko durch `fluent-datetime`); `fluent-datetime` nur erwägen, wenn Vorlagen `DATETIME` selbst steuern sollen, dann mit `jiff`.
3. CI-Prüfung (ADR-010 Punkt 4) selbst bauen: gleiche Nachrichten-IDs und Variablen je Sprache über `fluent-syntax` (Rust) bzw. `@fluent/syntax` (Browser).
4. Abhängigkeitspflege in `deny.toml` (K-Lieferkette) beobachten; Updates von `@fluent/bundle` wegen unveröffentlichter Breaking Changes erst nach Changelog-Lesen.

## Nicht geprüft

Tatsächliche Kompilierbarkeit von `fluent-bundle` 0.16 und `fluent-datetime` 0.2 zusammen mit `icu` 2.4 im Chronos-Workspace (kein Spike). Aussagen zur Pflege stammen aus Registry-/GitHub-Metadaten, nicht aus Code-Review.
