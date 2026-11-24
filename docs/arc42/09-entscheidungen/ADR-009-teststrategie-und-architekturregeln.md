---
id: ADR-009
title: Teststrategie und Architekturregeln: Cargo-Workspace mit einem Crate je Baustein
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-016]
quellen: [QA-003, RB-007, ADR-002, ADR-004, ADR-005, ADR-007, Rust-Spike E-002 (tools/arch-check.sh), Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-009: Teststrategie und Architekturregeln: Cargo-Workspace mit einem Crate je Baustein

**Hinweis:** Der Product Owner hat die Entscheidung am 2026-11-24 im Gespräch getroffen. Dieser Text wurde vom Product Owner am 2026-11-24 freigegeben.

## Kontext
Die Zerlegung ([ADR-002](ADR-002-zerlegung-monolith-plus-worker.md)) und die Operationsschicht ([ADR-005](ADR-005-operationsschicht.md)) leben von Abhängigkeitsregeln (z. B. „Fachbereiche erreichen Adapter nicht“, „domain kennt channels nicht“). Der Spike hat sie mit einem `grep`-Skript geprüft (`tools/arch-check.sh`). Eine Regel, die nur so gut ist wie ein Skript, ist bei einem Ein-Personen-Team mit Agenten (RA-003) die Schwachstelle, weil Agenten Regeln verletzen, wenn nichts sie daran hindert.

## Optionen
- **A** Cargo-Workspace, ein Crate je Baustein (core, domain, channels, web, worker): Regel vom Compiler erzwungen, Zyklen unmöglich, paralleles und inkrementelles Bauen; mehr `Cargo.toml`, Orphan-Regel erzwingt manchmal Hilfstypen, Umzüge zwischen Crates aufwendiger. Vergleichbar mit Maven-Modulen bzw. JPMS statt ArchUnit.
- **B** Ein Crate, Sichtbarkeit (`pub(crate)`) und Skript wie im Spike: einfach und belegt, aber `grep` übersieht Makros, Re-Exporte und voll qualifizierte Pfade.
- **C** A für harte Grenzen plus `cargo-deny` (`bans`) für verbotene Bibliotheken je Crate: doppelte Absicherung, zwei Mechanismen zu pflegen.

## Entscheidung (PO, 2026-11-24)
**Option A.** Ein Cargo-Workspace mit einem Crate je Baustein; die Abhängigkeitsregeln stehen in den `Cargo.toml` und werden vom Compiler erzwungen. Der genaue Zuschnitt der Crates folgt aus der Bausteinsicht ([Kapitel 5](../05-bausteine/01-bausteinsicht.md)); die fünf Spike-Bausteine (core, domain, channels, web, worker) sind der Ausgangspunkt. Der Zuschnitt (sieben Crates, mit `adapters` und dem Binary `chronos`) steht im [Crate-Zuschnitt](../05-bausteine/02-crate-zuschnitt.md).

**Testebenen (Vorschlag des Entwurfs, vom Product Owner übernommen):**
1. Unit-Tests im Modul.
2. Datenbanktests mit `#[sqlx::test]` gegen echtes PostgreSQL (je Test eine frische Datenbank, statt Testcontainers).
3. Szenariotests aus [Kapitel 6](../06-laufzeit/) über HTTP (`tower::ServiceExt::oneshot`, ohne Netz).
4. Differenztest der RRULE-Auswertung gegen python-dateutil und Property-Tests (`proptest`) für Serien.
5. Snapshot-Tests (`insta`) für Operations- und Werkzeugschemas, damit Schemaänderungen im Review sichtbar werden.
6. Oberflächentests mit Playwright über Rollen und Beschriftungen, dazu axe-core (WCAG 2.2 AA), nach [ADR-007](ADR-007-frontend-spa-svelte.md) V-5.
7. Läufer `cargo-nextest`; `sqlx::query!` prüft SQL beim Übersetzen (in CI mit `.sqlx`-Dateien).

## Folgen
**Leichter:** Verletzungen der Schichtregeln scheitern beim Übersetzen, auch bei Agenten; kein Zusatzwerkzeug für die Regeln; paralleles Bauen.

**Schwerer:** Mehr Dateien und Konfiguration; Zuschnitt der Crates vor der Umsetzung nötig (Zyklen vermeiden); ein Umzug zwischen Crates kostet mehr als zwischen Modulen; Orphan-Regel kann Hilfstypen erzwingen.

**Bindet / gibt frei:** Die offene Entscheidung zu Build, CI und Lieferkette (`cargo-deny` als CI-Prüfung für Advisories, Lizenzen und Quellen) bleibt unabhängig und ist nicht Teil dieser ADR. Der Differenztest RRULE aus ADR-004 ist hier als Testebene festgehalten.

## Wann überprüfen?
- Die Zahl der Crates oder die Bauzeit wird zum Problem (dann Zusammenlegen).
- Eine Regel lässt sich im Workspace nicht ausdrücken (dann `cargo-deny` oder ein Test als Ergänzung, Option C).
- Der Zuschnitt der Bausteine ändert sich grundlegend (ADR-002).
