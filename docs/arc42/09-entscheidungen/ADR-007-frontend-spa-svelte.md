---
id: ADR-007
title: Frontend als SPA mit Svelte, Gastseite als eigener Einstieg, UI-Schicht austauschbar
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-004]
quellen: [E-004-E-008-frontend-und-zugang-analyse, E-004-frontend-auswahl, QA-005, QA-008, Z-004, RB-001, RB-011, FA-002, FA-005, K-007, ADR-001, ADR-002, ADR-004, ADR-005, ADR-006, Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-007: Frontend als SPA mit Svelte, Gastseite als eigener Einstieg, UI-Schicht austauschbar

**Hinweis:** Der Product Owner hat die Entscheidung am 2026-11-24 im Gespräch getroffen. Dieser Text wurde vom Product Owner am 2026-11-24 freigegeben. E-008 (Sitzung, Gast-Identität) ist **nicht** Teil dieser ADR, sondern in [ADR-008](ADR-008-sitzung-und-gast-identitaet.md) geregelt (siehe Folgen).

## Kontext
Die Oberfläche ist mobil zuerst, bewusst einfach ([RB-011](../../req42/07-randbedingungen/)) und braucht Interaktivität nur bei Assistent-Dialog, Stapel-Vorschau und Terminfindung. Die wichtigste Seite ist die Gastseite ([Z-004](../../req42/)): Link aus dem Messenger, kalter Cache, Mobilnetz, höchstens drei Interaktionen ([QA-005](../../req42/), [QA-008](../../req42/) < 1 s). Der Web-Prozess ist Rust ([ADR-004](ADR-004-sprache-und-laufzeit.md)), ein Node-Prozess zur Laufzeit ist ausgeschlossen ([ADR-002](ADR-002-zerlegung-monolith-plus-worker.md), G0). Die Operationsschicht liefert eine maschinenlesbare Beschreibung, aus der TypeScript-Typen entstehen ([ADR-005](ADR-005-operationsschicht.md)).

## Optionen
Ausführlich in der [Analyse](E-004-E-008-frontend-und-zugang-analyse.md) (V1 SPA, V2 Server-Rendering, V3 SPA mit Refresh-Token) und der [Auswahlliste](E-004-frontend-auswahl.md) (fünf Stile, Shortlist Svelte, askama + htmx, Leptos). Für die Gastseite wurden fünf Varianten betrachtet: **A** eigener Svelte-Einstieg, B server-gerendert mit Progressive Enhancement, C vorgerenderte Hülle mit Hydration, D eigenständiges Mini-Bundle, E Plain TypeScript.

## Entscheidung (PO, 2026-11-24)
1. **Ansatz V1:** Single-Page-Application als PWA, statisch gebaut und vom Web-Prozess unter **derselben Herkunft** ausgeliefert. Anmeldung und Sitzung über Cookie (Einzelheiten in E-008).
2. **Framework: Svelte 5 mit statischem Build**, ohne Auswahl-Spike. Begründung: kleinste Bundles ▲, Barrierefreiheitsprüfung im Compiler, passt zu G0.
3. **Gastseite: Variante A.** Eigener Einstiegspunkt der SPA (eigene HTML-Datei im Build, kein Router, eigenes Größenbudget). Der Server bettet die Termindaten vorab als JSON in die HTML-Antwort ein. Das Link-Token liegt im **Fragment** der Adresse; ein Token im Pfad ist **nicht zulässig**. Dass die Gastseite ohne JavaScript funktioniert, ist **keine** Anforderung.
4. **Austauschbarkeit:** Die UI-Schicht (Svelte) muss mit begrenztem Preis gegen Vue oder Angular austauschbar bleiben, und die Gastseite muss später ohne großen Aufwand auf Server-Rendering (Variante B) umstellbar sein. Dafür gelten die folgenden Architekturvorgaben.

### Architekturvorgaben (Austauschbarkeit der UI-Schicht)
- **V-1 Framework-freies Paket:** API-Client (`call(name, params)`), generierte Typen, Sitzungs- und Gast-Logik, Fehlercode-Abbildung, Formatierung und Validierung liegen in einem eigenen TypeScript-Paket **ohne** Svelte-Import. Komponenten rendern nur und rufen dieses Paket auf.
- **V-2 Svelte sparsam:** SvelteKit nur für Routing und statischen Adapter; keine `load`-Funktionen mit Serverbezug, keine Svelte-Stores in der Logik des Pakets aus V-1.
- **V-3 Übersetzungen:** Fluent (`.ftl`) in Server und Client, getrennt nach UI, Gastseite und Benachrichtigungen; die Bindung an die Bibliothek ist dünn gehalten. Ein Test prüft die Vollständigkeit beider Sprachen. *(Geändert am 2026-11-24 durch [ADR-010](ADR-010-uebersetzungen-fluent.md); vorher: JSON mit ICU-Syntax.)*
- **V-4 Gestaltung:** Farben, Abstände und Schrift als CSS-Variablen in einer gemeinsamen Datei `tokens.css`; Gestaltung der Gastseite in einer **einfachen CSS-Datei**, nicht in komponentengebundenen Svelte-Stilen.
- **V-5 Abnahme:** Playwright-Tests sprechen die Oberfläche **nur über Rollen und Beschriftungen** an (`getByRole`, `getByLabel`), dazu axe-core (WCAG 2.2 AA). Sie sind die Abnahme für jeden Wechsel des Frameworks und für Variante B der Gastseite.

### Vorgaben für die Gastseite (Vorbereitung auf Variante B)
- **G-1 Eigene Schnittstelle:** Die Gastseite nutzt nur drei einfache Aufrufe: Token gegen Gast-Sitzung tauschen, Termin lesen, Antwort speichern. Sie sind unabhängig von der Oberfläche, und ein Server-gerendertes HTML könnte sie unverändert verwenden.
- **G-2 Sicht-Modell auf dem Server:** Der Server erzeugt für die Gastseite ein typisiertes Sicht-Modell (Rust-Struktur: Termin, Antworten, Zustand der Antwort, Rückkehr-Link). Bei A wird es als JSON eingebettet, bei B an eine Vorlage übergeben.
- **G-3 Einfaches HTML:** Echtes `<form>` mit Radiogruppe (`fieldset`/`legend`, `input type="radio"`), Beschriftungen, keine eigenen Bedienelemente. Die Svelte-Komponente stellt nur dieses Markup dar und enthält keine Logik außer der Anbindung an V-1.
- **G-4 Texte der Gastseite** in einer eigenen kleinen `.ftl`-Datei (ca. 20 Einträge), damit sie später in den Server-Katalog wandern kann.
- **G-5 Größenbudget** für den Einstiegspunkt (Bytes komprimiert, Zeit bis zur bedienbaren Seite), im Build geprüft, damit die Messgrößen MF-1 bis MF-4 der Auswahlliste dauerhaft erfüllt bleiben.
- **Hinweis zu B:** Bei einem späteren Wechsel bleibt das Token im Fragment. Ein winziges Skript tauscht es gegen das Cookie und lädt neu; ab dann rendert der Server. Ohne JavaScript wäre nur der **erste** Besuch nicht möglich, was keine Anforderung verletzt.

## Folgen
**Leichter:** Typisierte Brücke, Assistent-Streaming, Stapel-Vorschau und Terminfindung natürlich umsetzbar; Änderungen an der UI ohne Rust-Build; Framework nur in der UI-Schicht gebunden.

**Schwerer / Risiken:**
- N1 (Inhalt erst nach JavaScript): gemildert durch eingebettetes JSON und Größenbudget, aber nicht beseitigt.
- N4 Barrierefreiheit: Fokus und Ansage bei Seitenwechseln sind einmal im Router-Wrapper zu lösen (Fokus auf H1, `aria-live="polite"`).
- N5 zweite Werkzeugkette: Lockfile, Abhängigkeiten zählen, Pipeline-Prüfung wie bei ADR-004.
- N6 zwei Übersetzungskataloge: getrennte Verzeichnisse und Vollständigkeitstest.
- Svelte hat Brüche zwischen Hauptversionen (4 → 5, SvelteKit 2 → 3): Versionen festschreiben, Upgrades bewusst einplanen.
- Ein Wechsel auf Vue wäre mittelgroß, auf Angular groß (anderes Paradigma); die UI-Komponenten sind in jedem Fall neu zu schreiben.
- Neue Risiken für Kapitel 11: Größenbudget der Gastseite verfehlt; Svelte-Hauptversionsbruch.

**Bindet / gibt frei:**
- E-008 ist **nicht** entschieden. Die Entscheidung setzt voraus: Cookie-Sitzung unter derselben Herkunft, Token im Fragment (T3-A). Offen bleiben Sitzungsdauer, Gast-Wiedererkennung (Rückkehr-Link), Back-Channel-Logout im Keycloak (SH-006) und WCAG-Maßstab (Fragen 3 bis 6 der Analyse).
- E-016 (Teststrategie) bekommt die Playwright- und axe-Vorgaben aus V-5.
- Der Generator der Brücke soll nicht gegen einen laufenden Server arbeiten, sondern gegen eine vom Binary geschriebene Datei (siehe Analyse, Brücke).
- Die Spikes aus der Auswahlliste (F-1) entfallen.

## Festgelegte Werte (PO, 2026-11-24)
- **Größenbudget Gastseite (G-5):** Einstieg höchstens 60 KB komprimiert übertragen, LCP höchstens 1,0 s bei gedrosseltem Mobilnetz (Lighthouse „Slow 4G“); im Build geprüft.
- **Größenbudget Haupt-SPA:** Erstladung höchstens 200 KB komprimiert ▲ (Startgrenze, nach dem ersten Durchstich anzupassen).

## Wann überprüfen?
- Das Größenbudget der Gastseite ist auf realen Geräten nicht erreichbar, oder die Zeit bis zur bedienbaren Seite verfehlt QA-008 deutlich.
- Eine Anforderung verlangt, dass die Gastseite ohne JavaScript nutzbar ist (dann Variante B).
- Svelte wird nicht mehr gepflegt oder ein Hauptversionsbruch ist unverhältnismäßig teuer.
- Es kommen viele interaktive Seiten außerhalb von Assistent, Vorschau und Terminfindung hinzu, oder umgekehrt wird die Oberfläche überwiegend einfache Listen und Formulare.
