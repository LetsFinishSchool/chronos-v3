---
id: ADR-012
title: Zeitbibliothek: jiff im Fachkern, chrono nur an den Rändern
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-020]
quellen: [ADR-004, ADR-009, K-007, FA-003, FA-014, wiki/concepts/e-002-folgeentscheidungen-rust (Abschnitt 8), E-002a (jiff statt rrule), RUSTSEC-Meldungen zu chrono und chrono-tz, Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-012: Zeitbibliothek: jiff im Fachkern, chrono nur an den Rändern

**Hinweis:** Der Product Owner hat die Entscheidung am 2026-11-24 im Gespräch getroffen. Dieser Text wurde vom Product Owner am 2026-11-24 freigegeben. Die neue Nummer E-020 ist in Kapitel 9 ergänzt.

## Kontext
Termine, Zeitzonen und Sommerzeit sind der Kern ([FA-003](../../req42/04-product-backlog/anforderungen/FA-003-termine.md), [FA-014](../../req42/04-product-backlog/anforderungen/)): Zeitpunkt in UTC plus Zeitzone des Termins, Serien bleiben über die Sommerzeit lokal stabil ([K-007](../08-konzepte/K-007-mehrsprachigkeit-und-zeitzonen.md)), Zeitzonendaten sind regelmäßig zu aktualisieren. Der Spike nutzt `chrono` und `chrono-tz`; beide gelten laut RUSTSEC als „unmaintained“, `chrono-tz` ist archiviert. `rrule` hängt an `chrono` und wurde in [ADR-004](ADR-004-sprache-und-laufzeit.md) behalten und isoliert. Das Experiment E-002a (`jiff` statt `rrule`) kostete 298 Zeilen Eigenbau (12,5 %).

## Optionen
A `chrono` + `chrono-tz` überall; B `jiff` überall; **C `jiff` im Fachkern, `chrono` nur an den Rändern**. Vor- und Nachteile in der Entscheidungsvorlage vom 2026-11-24 und in `wiki/concepts/e-002-folgeentscheidungen-rust.md`, Abschnitt 8.

## Entscheidung (PO, 2026-11-24)
**Option C.**
1. **Fachkern** (Termine, Zeitzonen, Sommerzeit, Erinnerungsplanung, Anzeige) verwendet ausschließlich `jiff`; kein `chrono` im Fachkern-Crate (Compiler-erzwungen über die Abhängigkeiten, [ADR-009](ADR-009-teststrategie-und-architekturregeln.md)).
2. **Ränder** (`rrule`, `sqlx`, ggf. `utoipa`/`schemars`) dürfen `chrono` nutzen. Die Umrechnung zwischen den Zeittypen liegt in **einem** Adapter-Modul an der Grenze und ist durch Tests abgesichert.
3. **Zeitzonendaten:** eingebettet über `jiff-tzdb` (siehe „Festgelegte Werte“), regelmäßig zu aktualisieren (K-007). Der Fachkern und die Ränder dürfen nicht zu unterschiedlichen Zeitzonendaten führen; ein Test deckt Sommerzeit-Übergänge ab.
4. Der Differenztest der Serienauswertung gegen python-dateutil (ADR-009, Testebene 4) bleibt Pflicht.

## Folgen
**Leichter:** Der Fachkern hängt nicht am Pflegestand der archivierten Bibliothek; eindeutige Sommerzeit-Semantik; `rrule` bleibt isoliert wie in ADR-004.

**Schwerer / Risiken (für Kapitel 11):**
- Zwei Zeittypen mit Umrechnung an der Grenze: Fehler bei Sommerzeit-Übergängen und bei Zeitzonen, die in beiden Datenbanken abweichen.
- Zwei Zeitzonendatenbanken sind getrennt aktuell zu halten (`chrono-tz` bleibt archiviert, solange `rrule` daran hängt).
- Die Audit-Ausnahme für `chrono` und `chrono-tz` bleibt bestehen, ist aber auf die Ränder begrenzt und dokumentiert.

**Bindet:** [ADR-009](ADR-009-teststrategie-und-architekturregeln.md) (Crate-Grenze zwischen Fachkern und Rändern); Build und Lieferkette (Ausnahmen in `deny.toml`, noch zu entscheiden).

## Festgelegte Werte (PO, 2026-11-24)
- **Zeitzonendaten im Fachkern:** `jiff` mit eingebetteter Datenbank (`jiff-tzdb`, Feature `tzdb-bundle-always`), unabhängig von der Systemdatenbank des Images. Aktualisierung über Dependency-Updates (Renovate oder Dependabot) und den monatlichen Image-Neubau; der Pflegestand ist geprüft (siehe unten).
- **Prüfung 2026-11-24 (Pflegestand, [Wiki](../../../wiki/concepts/jiff-tzdb-pflegestand.md)):** `jiff` und `jiff-tzdb` sind aktiv gepflegt. `jiff-tzdb` übernimmt neue IANA-Releases mit unregelmäßigem Verzug (meist 1 Tag, bei 2026b 70 Tage, bei 2026f 17 Tage). Regeländerungen mit kurzer Vorlaufzeit können daher mit Verzug im Binary ankommen; Renovate/Dependabot und der monatliche Image-Neubau (ADR-013) mildern das.
- **Eingebettet erzwingen:** `jiff::tz::db()` nutzt zuerst die Systemdatenbank, die eingebettete ist nur Rückfall (und `distroless/cc` enthält `tzdata`). Der Fachkern löst Zeitzonen daher über `TimeZoneDatabase::bundled()` auf, gekapselt im Adapter. Beim Start wird `jiff_tzdb::VERSION` geloggt, ein Test prüft, dass die eingebettete Version benutzt wird.
- **Ränder:** `chrono-tz` bleibt für `rrule`; ein Test der Sommerzeit-Übergänge vergleicht beide Zeitzonendatenbanken.

## Wann überprüfen?
- `rrule` wird nicht mehr gepflegt oder ersetzt (dann `jiff` überall, Option B).
- `chrono-tz` bekommt einen Nachfolger oder die Ausnahme im Audit wird untragbar.
- Fehler an der Grenze zwischen den Zeittypen treten gehäuft auf.
