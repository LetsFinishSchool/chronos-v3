---
id: ADR-010
title: Übersetzungen mit Fluent in Server und Client
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-018]
quellen: [K-007, RB-001, E-004-E-008-frontend-und-zugang-analyse (T7), ADR-004, ADR-007, ADR-008, Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-010: Übersetzungen mit Fluent in Server und Client

**Hinweis:** Der Product Owner hat die Entscheidung am 2026-11-24 im Gespräch getroffen und die Niederschrift am selben Tag freigegeben, nachdem die Prüfung von Pflegestand und `DATETIME` (siehe „Prüfergebnis“) vorlag. Die Vorgabe „JSON oder PO“ in [K-007](../08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md) war nie eine Anforderung des Product Owners und entfällt. Die neue Nummer E-018 ist in Kapitel 9 ergänzt.

## Kontext
Oberflächentexte braucht der Client, Benachrichtigungstexte der Server (Worker, je Empfänger übersetzt); die Gastseite kann später in den Server wandern ([ADR-007](ADR-007-frontend-spa-svelte.md) G-4). Deutsch und Englisch, weitere Sprachen ohne Umbau ([RB-001](../../req42/07-randbedingungen/RB-001-mehrsprachigkeit.md)). Plural, Datum und Zahlen müssen in beiden Welten stimmen. ADR-007 V-3 hatte für die UI JSON mit ICU-Syntax vorgesehen; im Server gibt es dafür keinen stabilen Parser.

## Optionen
A JSON mit ICU-Syntax, im Server eigenes Nachschlagen mit ICU4X-Plural; **B Fluent (`.ftl`) auf beiden Seiten**; C gettext PO; D `rust-i18n` im Server mit eigenem Format im Frontend. Vor- und Nachteile der abgelehnten Optionen:

| Option | Vorteile | Nachteile |
|---|---|---|
| A JSON mit ICU MessageFormat, Browser vue-i18n/FormatJS | Frontend-Standard; Plattformen wie Weblate können es | Rust-Unterstützung für MessageFormat dünner; Gefahr eines zweiten Formats im Server |
| C gettext PO | Ausgereifte Übersetzungswerkzeuge (Poedit, Weblate) | Rust-Crates teils C-Bindungen; im Frontend unüblich; Pluralformeln als C-Ausdruck |
| D `rust-i18n` (YAML/JSON, Makro `t!`) im Server, eigenes Format im Frontend | Schnell eingerichtet, Schlüssel beim Übersetzen geprüft | Zwei Formate; Pluralregeln einfach |

Bei Server-Rendering (E-004 B) entfiele die Client-Seite; E-004 ist als SPA entschieden.

## Entscheidung (PO, 2026-11-24)
**Option B: Fluent in Server und Client.**

1. **Ein Format:** Übersetzungen als `.ftl`-Dateien je Sprache im Repository. Server: `fluent-rs`, Browser: `@fluent/bundle`. Plural- und Geschlechtsunterscheidungen stehen in der Nachricht selbst (Fluent-Selektoren, CLDR-Pluralregeln).
2. **Aufteilung (Vorschlag):** `i18n/<sprache>/` mit `ui.ftl` (Client), `guest.ftl` (Gastseite, Client und später Server) und `notifications.ftl` (Server). Fehlercodes der Operationsschicht werden im Client übersetzt ([ADR-005](ADR-005-operationsschicht.md)).
3. **Datum und Zahlen (Vorschlag):** Im Browser über die Fluent-Funktionen und `Intl`. Im Server formatiert Rust Datum und Zahl **vor** der Übergabe als Argument (ICU4X, in der Zeitzone des Termins bzw. der Person, [K-007](../08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md)), weil `fluent-rs` kein eingebautes `DATETIME` kennt (geprüft, siehe „Prüfergebnis“).
4. **Prüfungen in CI:** beide Sprachen enthalten dieselben Nachrichten mit denselben Variablen; Syntaxprüfung der Dateien auf beiden Seiten.

## Prüfergebnis (Stand 2026-11-24)
Geprüft über crates.io, npm und GitHub (Metadaten, kein Übersetzen im Workspace).

Weitere Befunde: `fluent-bundle` 0.16.0 und `fluent` 0.17.0 (2025-05-22/23) haben 67 offene Issues und seit Mai 2025 nur Lint- und Doku-Commits. `fluent-syntax` 0.12.0, `intl-memoizer` 0.5.3, `unic-langid` 0.9.6 und `fluent-langneg` 0.14.2 haben je etwa 25 bis 33 Mio. Downloads. `@fluent/bundle`: Der Hauptzweig enthält unveröffentlichte, teils inkompatible Änderungen (Vitest-Umstieg, `Intl.Locale` in langneg). `fluent-datetime` 0.2.0 (2026-02-21, Repo `g2p/fluent-datetime`, `add_datetime_support()`) und `icu` 2.4.0 (2026-10-22).

| Baustein | Stand | Bewertung |
|---|---|---|
| `fluent-bundle` 0.16.0, `fluent` 0.17.0 | Veröffentlicht 2025-05; Repo `projectfluent/fluent-rs` nicht archiviert, seither nur Lint- und Doku-Commits | Stabil, langsame Pflege, kein 1.0; breit genutzt (Mozilla, ~9,5 Mio. Downloads in 90 Tagen) |
| `@fluent/bundle` 0.19.1 | Veröffentlicht 2025-04; Repo `projectfluent/fluent.js` aktiv bis 2026-01, teils unveröffentlichte Breaking Changes | Gepflegt; vor Updates Changelog lesen |
| `DATETIME` im Browser | In `@fluent/bundle` eingebaut (über `Intl`) | Erfüllt |
| `DATETIME` im Server | In `fluent-bundle` nicht vorhanden, [fluent-rs#181](https://github.com/projectfluent/fluent-rs/issues/181) seit 2020 offen. Zusatzcrate `fluent-datetime` 0.2.0 (ICU4X 2 + `jiff`) mit einem Maintainer, ~12 000 Downloads | Entscheidung Punkt 3 (vorab formatieren) bestätigt; `fluent-datetime` nur bei Bedarf und dann mit `jiff` |
| Übersetzungsplattform | Weblate unterstützt `.ftl` (monolingual, Syntaxprüfungen), ohne Plural-Flags und Kontext | Ausreichend; Verhalten bei komplexen Selektoren ungeprüft |

Daraus folgt: Die Risiken „Pflegestand“ und „Plattform“ sind für den Start tragbar. Ungeprüft bleibt, ob `fluent-bundle` und `fluent-datetime` mit `icu` 2.x im Workspace zusammen übersetzen.

## Folgen
**Leichter:** Ein Format für Server und Client; die Gast-Texte können ohne Umformatierung vom Client in den Server wandern; Plural und Geschlecht liegen in der Nachricht, nicht im Code.

**Schwerer / Risiken:**
- Kleineres Ökosystem als JSON, gettext oder i18next; Weblate unterstützt Fluent, aber ohne Plural-Flags und Kontext (siehe „Prüfergebnis“).
- `fluent-rs` ist pre-1.0 und wird langsam gepflegt (letzte Veröffentlichung 2025-05); bei Umsetzungsbeginn den Stand erneut prüfen (wie Q-4 aus E-002).
- Die Prüfung gleicher Nachrichten und Variablen je Sprache (Entscheidung Punkt 4) ist eigener CI-Code über `fluent-syntax` bzw. `@fluent/syntax`.
- Datums- und Zahlenformatierung im Server ist eigener Code (ICU4X).
- Der Svelte-Anschluss an `@fluent/bundle` ist eigener, dünner Code, gemäß ADR-007 V-2 und V-3 klein zu halten.

**Ändert:** [ADR-007](ADR-007-frontend-spa-svelte.md) V-3 (JSON mit ICU-Syntax) entfällt zugunsten dieser ADR; [K-007](../08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md) (Format) und [ADR-008](ADR-008-sitzung-und-gast-identitaet.md) T7 sind angepasst. Die Anforderung „JSON oder PO“ in K-007 entfällt.

## Festgelegte Werte (PO, 2026-11-24)
Aufteilung (`ui.ftl`, `guest.ftl`, `notifications.ftl` je Sprache) und Datums- und Zahlenformatierung im Server vor der Übergabe (ICU4X) sind bestätigt (Punkte 2 und 3 der Entscheidung gelten als entschieden).

## Wann überprüfen?
- `fluent-rs` oder `@fluent/bundle` werden nicht mehr gepflegt, oder keine brauchbare Übersetzungsplattform unterstützt Fluent.
- Übersetzende arbeiten mit Werkzeugen, die nur JSON oder PO können.
- Datums- und Zahlenformatierung im Server wird aufwendiger als erwartet.
