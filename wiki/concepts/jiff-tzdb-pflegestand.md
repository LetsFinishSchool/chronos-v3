---
title: jiff-tzdb: Pflegestand und Auswahl der Zeitzonendatenbank (ADR-012)
type: concept
sources:
  - docs/arc42/09-entscheidungen/ADR-012-zeitbibliothek.md
  - crates.io-API (jiff, jiff-tzdb, jiff-tzdb-platform, chrono-tz), abgerufen 2026-11-24
  - Quelltext der Crates jiff-tzdb 0.1.7, 0.1.9, 0.1.10, 1.0.0 (Konstante VERSION) und jiff 1.0.3 (src/tz/db/mod.rs), heruntergeladen 2026-11-24
  - GitHub-API eggert/tz (Tags 2025c bis 2026f, Commit-Daten), BurntSushi/jiff (nicht archiviert, letzter Push 2026-11-24), abgerufen 2026-11-24
confidence: hoch (Versionen und Daten geprüft); mittel (Zuordnung der Veröffentlichungen 0.1.5, 0.1.6, 0.1.8 zu 2025c, 2026a, 2026c nur aus Daten abgeleitet)
last-verified: 2026-11-24
---

# jiff-tzdb: Pflegestand

Auftrag: ▲ aus ADR-012 („wie schnell übernimmt `jiff-tzdb` neue IANA-Releases?“). Ergebnis: **Pflege aktiv, Verzug unregelmäßig (1 Tag bis 70 Tage), und die eingebettete Datenbank wird nicht automatisch benutzt.**

## Pflege
- `jiff` 1.0.3 (2026-11-24), `jiff-tzdb` 1.0.0 (2026-11-15), Repo nicht archiviert, letzter Push heute. Zum Vergleich `chrono-tz` 0.10.4 seit 2025-07-11 ohne Release.
- Das Crate trägt die IANA-Version in der Konstante `jiff_tzdb::VERSION`.

## Verzug gegenüber IANA (eggert/tz)
| IANA-Release | Datum | jiff-tzdb | Datum | Verzug |
|---|---|---|---|---|
| 2025c | 2025-12-10 | 0.1.5 | 2025-12-11 | 1 Tag (abgeleitet) |
| 2026a | 2026-03-02 | 0.1.6 | 2026-03-03 | 1 Tag (abgeleitet) |
| 2026b | 2026-04-23 | 0.1.7 (enthält 2026b, geprüft) | 2026-07-02 | **70 Tage** |
| 2026c | 2026-07-08 | 0.1.8 | 2026-07-09 | 1 Tag (abgeleitet) |
| 2026d | 2026-09-11 | übersprungen | | |
| 2026e | 2026-09-30 | 0.1.9 (enthält 2026e, geprüft) | 2026-10-06 | 6 Tage |
| 2026f | 2026-10-28 | 0.1.10 und 1.0.0 (enthalten 2026f, geprüft) | 2026-11-14 | 17 Tage |

Folge: Eine Regeländerung mit kurzer Vorlaufzeit kann mit mehreren Wochen Verzug im Binary ankommen. Gegenmaßnahmen: Renovate/Dependabot, monatlicher Image-Neubau (ADR-013); bei dringender Änderung ein manuelles Update.

## Wichtig: eingebettet ist nicht automatisch benutzt
`jiff::tz::db()` nutzt `TimeZoneDatabase::from_env()`. Das sucht **zuerst die Systemdatenbank** (`/usr/share/zoneinfo`, `TZDIR`) und nimmt die eingebettete nur als Rückfall. Das Feature `tzdb-bundle-always` stellt die eingebettete Datenbank nur **bereit**. Das Image `distroless/cc` enthält `tzdata`; dort würde die Systemdatenbank gewinnen. Um die eingebettete zu erzwingen, ist `TimeZoneDatabase::bundled()` ausdrücklich zu verwenden und Zeitzonen darüber aufzulösen (im Adapter für den Fachkern kapseln). Ob ein leeres oder falsches `TZDIR` genügen würde, ist ungeprüft ▲.

## Folgerungen
1. ADR-012 um den Hinweis ergänzen (geschehen): `TimeZoneDatabase::bundled()` verwenden.
2. Beim Start `jiff_tzdb::VERSION` loggen und im Betrieb sichtbar machen; ein Test prüft, dass der Fachkern die eingebettete Version benutzt.
3. Der Vergleichstest der Sommerzeit-Übergänge (jiff gegen `chrono-tz`) zeigt zusätzlich, wenn die beiden Datenbanken auseinanderlaufen (`chrono-tz` ist auf dem Stand von 2025-07).
