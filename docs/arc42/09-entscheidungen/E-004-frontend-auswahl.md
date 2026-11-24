---
title: E-004 Frontend, Auswahlliste und Spike-Plan
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
quellen: [E-004-E-008-frontend-und-zugang-analyse, ADR-002, ADR-004, ADR-005, ADR-006, QA-005, QA-008, Z-004, RB-001, RB-011, K-007, npm-Registry und crates.io (abgefragt 2026-11-23), Rust-Spike E-002]
---

# E-004: Frontend, Auswahlliste und Spike-Plan

Ergänzt die [gemeinsame Analyse E-004/E-008](E-004-E-008-frontend-und-zugang-analyse.md). Anlass: Der Product Owner empfindet die vorgeschlagene Variante V1 (SPA mit eigener Sitzung) als „unsauber“ und verlangt eine Framework-Wahl **nach technischer Eignung, nicht nach Vertrautheit**. Versionen und Pflegeangaben stammen aus der npm-Registry und crates.io (2026-11-23). Größen- und Leistungsangaben mit ▲ sind Größenordnungen und werden im Spike gemessen.

## 1. Woher das Gefühl „unsauber“ kommt

Geprüft wird jede mögliche Ursache: Ist sie ein Fakt, und ist sie ein Nachteil **von V1** oder gilt sie für jede Variante?

| Mögliche Ursache | Fakt? | Echter Nachteil von V1? | Bewertung |
|---|---|---|---|
| **Gastseite passt schlecht zur SPA.** Die wichtigste Seite (Z-004: Link aus dem Messenger, erster Besuch, kalter Cache, Mobilnetz) ist genau die, für die eine SPA am schlechtesten ist: Erst kommt eine leere Hülle, dann JavaScript, dann die Daten. Der Vorschlag „eigener kleiner Einstieg per Code-Splitting“ ist ein Umweg um dieses Problem. | ja | **ja** | Stärkster Punkt. Bei Server-Rendering steht der Termin in der ersten Antwort. |
| **Werkzeug größer als die Aufgabe.** RB-011 verlangt eine bewusst einfache Oberfläche; die meisten Seiten sind Listen und Formulare. Echte Interaktivität gibt es an drei Stellen: Assistent-Dialog, Vorschau und Freigabe von Stapeln, Terminfindung. Eine SPA macht dagegen *jede* Seite zu Client-Code mit Router, Zustand und Build. | ja | **ja** | Spricht für „Server zuerst, Inseln wo nötig“. |
| **Barrierefreiheit muss nachgebaut werden.** Bei einer SPA setzt der Browser Fokus und Ansage beim Seitenwechsel nicht selbst; das muss die Anwendung tun (WCAG 2.4.3, 4.1.3). Bei echter Navigation macht es der Browser. | ja | **ja** | Mehr Arbeit und eine zusätzliche Fehlerquelle, aber lösbar. |
| **Zwei Sprachen, zwei Werkzeugketten, zwei Lieferketten** (Rust/cargo und TypeScript/npm). | ja | ja, gemildert | Der Service Worker für Web Push ist in *jeder* Variante JavaScript. Bei einer SPA wächst daraus aber ein vollständiger npm-Build mit einigen hundert Entwicklungsabhängigkeiten. |
| **Zwei Übersetzungskataloge mit zwei Pluralschreibweisen** (Oberfläche im Client, Benachrichtigungen im Server). | ja | ja | Bei Server-Rendering in Rust können Oberfläche und Benachrichtigungen einen Katalog und ein Format teilen. |
| **Framework nach Vertrautheit vorgeschlagen** (Vue „dem Product Owner vertraut“). | ja | ja (Begründung) | Die Begründung war fachfremd. Abschnitt 3 ersetzt sie. |
| **Brücke wird zur Laufzeit erzeugt:** Der Generator des Spikes holt `/api/v1/operations` von einem laufenden Server und braucht Node und Netz. | ja | nein | Behebbar und unabhängig von V1: Das Binärprogramm schreibt die Operationsbeschreibung als Datei, Typen entstehen beim Build, ein Test prüft den Gleichstand. |
| **„Doppelte Sitzung“** (Keycloak und Chronos). | ja | nein | Das ist das empfohlene Muster *Backend for Frontend* für Browser-Anwendungen: Tokens bleiben im Server (C9). Echter Nachteil nur ohne Back-Channel-Logout (Sperre wirkt verzögert). Gilt für jede Variante mit Cookie-Sitzung. |
| **Link-Token im Fragment plus Austausch per Skript** wirkt wie ein Trick. | ja | nein | Etabliertes Muster: Das Fragment wird nicht an den Server und nicht im `Referer` übertragen. Nachteil nur: Ohne JavaScript keine Antwort. Bei Server-Rendering stattdessen Token im Pfad mit Maskierung in Protokollen. |
| **Gast mit Cookie *und* Rückkehr-Link** wirkt doppelt. | ja | nein | Folgt aus den Anforderungen (geteilter Link, kein Konto, mehrere Geräte), in jeder Variante gleich. |
| **Ein Web-Prozess für API, Oberfläche, Anmeldung, Assistent.** | ja | nein | So gewollt (ADR-002). Statische Dateien auszuliefern kostet im Prozess praktisch nichts. |
| **Web Push auf iOS nur in installierter PWA** ▲. | wahrscheinlich | nein | Gilt für jede Variante. |

**Ergebnis:** Das Gefühl beruht überwiegend auf echten Nachteilen. Die stärksten (Gastseite, Werkzeug größer als Aufgabe, Barrierefreiheit, zwei Kataloge) zeigen in **dieselbe Richtung**: Eine reine SPA passt schlecht zu einer Oberfläche, die überwiegend einfach ist, oft über einen Link betreten wird und nur an wenigen Stellen viel Interaktion braucht. Die Punkte zur Sitzung, zum Fragment-Token und zur Gast-Mechanik sind dagegen **keine** Schwächen von V1; sie bleiben in jeder Variante. E-008 ist davon kaum berührt, E-004 dagegen stark.

## 2. Kriterien (nur technisch)

Gewichtung nach ADR-001 (Änderbarkeit > Bedienbarkeit > Ressourcen > Benachrichtigung > Nachvollziehbarkeit).

| Nr. | Kriterium | Herleitung | Ziel |
|---|---|---|---|
| G0 | **K.o.:** kein Node-Prozess zur Laufzeit; Auslieferung durch den Web-Prozess (axum) oder als statische Dateien | ADR-002, RB-003 | – |
| G1 | Gastseite: Inhalt in der ersten Antwort, wenig JavaScript, ≤ 3 Interaktionen, < 1 s | Z-004, QA-005, QA-008 | Bedienbarkeit (2), Ressourcen (3) |
| G2 | Interaktive Stellen: Assistent mit Zwischenständen (Streaming), Vorschau und Freigabe von Stapeln, Terminfindung | ADR-005, ADR-006, FA-006 | Bedienbarkeit (2) |
| G3 | Typsicherheit zur Operationsschicht (generierte TS-Typen oder Rust-Typen direkt) | ADR-005, Q-5 aus E-002 | Änderbarkeit (1) |
| G4 | Barrierefreiheit: Grundverhalten (Navigation, Fokus), zugängliche Bausteine, Prüfwerkzeuge | T8, DoD | Bedienbarkeit (2) |
| G5 | Mehrsprachigkeit: ein Format, Plural, Datum in Termin-Zeitzone; Server-Benachrichtigungen | RB-001, K-007 | Änderbarkeit (1) |
| G6 | PWA und Service Worker | Produktvision, FA-008 | in allen Stilen gleich, kaum unterscheidend |
| G7 | Werkzeugketten und Lieferkette: Zahl der Sprachen und Builds, Abhängigkeiten | ADR-004 Folgen, RA-003 | Änderbarkeit (1) |
| G8 | Rückkopplung bei UI-Änderungen (Neuladen ohne vollen Rust-Build?) | E-002 M-7 | Änderbarkeit (1) |
| G9 | Stabilität der API und Agentenfähigkeit (Verbreitung, Brüche zwischen Hauptversionen) | ADR-001 Rang 1, RA-003 | Änderbarkeit (1) |
| G10 | Pflegestand (Releases, Maintainer, Trägerschaft) | Q-4 aus E-002 | Änderbarkeit (1) |

## 3. Auswahlliste

Gruppiert nach **Architekturstil**, weil der Stil mehr entscheidet als das einzelne Framework.

### Stil S1: Single-Page-Application (Client rendert alles)

Gemeinsam: G3 sehr gut (generierte TS-Typen), G2 sehr gut; G1, G4 und G5 schwächer (siehe Abschnitt 1); npm-Build.

| Kandidat (Version) | Vorteile | Nachteile |
|---|---|---|
| **Vue 3** (3.5.46; Vite 8) | Reife, stabile API seit 3.0; Vapor-Modus angekündigt; vue-i18n mit Plural; großes Ökosystem; viel Vorbild-Code | Mittlere Laufzeitgröße ▲; Barrierefreiheit von Komponentenbibliothek abhängig; npm-Paket von 2 Maintainern eingetragen (Organisation dahinter) |
| **React** (19.3.1) | Größtes Ökosystem, beste Agentenkenntnis; zugängliche Headless-Bibliotheken (React Aria) sehr ausgereift | Größte Laufzeit unter den Kandidaten ▲; Ökosystem drängt zu Server-Komponenten mit Node (Next), das passt nicht zu G0 |
| **Preact** (11.2.0) | Sehr klein ▲; React-kompatible API | Kleineres eigenes Ökosystem; Kompatibilitätsschicht zu React-Bibliotheken nicht lückenlos |
| **Svelte 5 / SvelteKit** (5.59.1 / 3.4.0, statischer Adapter) | Übersetzt zu kleinem JS ▲; der Compiler warnt bei Barrierefreiheitsfehlern; dateibasiertes Routing und Vorrendern statischer Seiten (Rechtsseiten, Hülle der Gastseite) | Brüche zwischen Hauptversionen (Svelte 4 → 5 „Runes“, SvelteKit 2 → 3); weniger Vorbild-Code mit Runes ▲ |
| **Solid** (2.0.3) | Sehr klein und schnell, feingranulare Reaktivität | Eingetragener npm-Maintainer: 1; 2.0 ist neu (Bruch); kleines Ökosystem |
| **Angular** (22.3.0) | Alles aus einer Hand (Router, Formulare, i18n, CDK mit A11y-Hilfen); strenge Struktur | Schwergewichtig für eine einfache mobile Oberfläche ▲; jährliche Hauptversionen; SSR nur mit Node |
| **Lit / Web Components** (3.3.3) | Standardnah, klein, als Inseln überall einbettbar | Kein Anwendungs-Framework (Router, i18n selbst); Shadow DOM erschwert Barrierefreiheit (ARIA-Verweise über Schattengrenzen funktionieren nicht) |
| **Ohne Framework** (TypeScript + DOM) | Keine Laufzeitabhängigkeit | Router, Zustand, i18n, Formulare als Eigenbau; widerspricht „wenig Eigenbau“ |

### Stil S2: Statisch vorgerendert mit Inseln (ohne Node zur Laufzeit)

Gemeinsam: Seiten werden **beim Build** erzeugt. Daten je Person (Termine, Antworten) können ohne Node-Server nicht serverseitig eingesetzt werden und kommen per Client-Abruf. G1 ist damit nur für die Hülle besser als bei S1.

| Kandidat (Version) | Vorteile | Nachteile |
|---|---|---|
| **Astro** (7.4.13, statische Ausgabe) | Inseln mit beliebigem Framework; null JS, wo keine Insel ist | Für Inhaltsseiten gebaut; für eine App mit Daten je Person entsteht eine Mehrseiten-Anwendung aus Mini-SPAs; SSR nur mit Node (G0) |
| **Nuxt** (4.6.4, `generate`) / **Next** (16.4.6, statischer Export) | Bekannte Strukturen | Statischer Modus schneidet die eigentlichen Stärken ab; Next-Export für Apps eingeschränkt; Nuxt-Paket mit 1 eingetragenem Maintainer |
| **Qwik** (1.20.4; 2.0 als RC) | „Resumability“: fast kein JS beim Start | Vorteil nur mit SSR (Node); 2.0 noch nicht stabil; kleines Ökosystem |

### Stil S3: Server-Rendering in Rust (Hypermedia)

Gemeinsam: HTML entsteht im Web-Prozess, direkt aus der Operationsschicht (kein HTTP-Umweg); G1, G4 und G5 sehr gut (echte Navigation, ein Übersetzungskatalog mit den Benachrichtigungen); G3 über Rust-Typen in den Vorlagen; G2 ist die Schwachstelle.

| Kandidat (Version) | Vorteile | Nachteile |
|---|---|---|
| **askama** (0.16.1) **+ htmx** (2.0.11; 4.0 als „next“) | Vorlagen werden beim Übersetzen geprüft (Felder, Typen); htmx klein ▲ und sehr verbreitet; Teilersetzungen ohne eigenen Client-Code | Jede Vorlagenänderung braucht einen Rust-Build (G8); htmx-Paket mit 1 eingetragenem Maintainer; htmx 4 ist ein angekündigter Bruch; Streaming des Assistenten über eine SSE-Erweiterung, Stapel-Vorschau als Fragmente |
| **minijinja** (3.1.0) **+ htmx** | Vorlagen zur Laufzeit neu ladbar (schnelle Rückkopplung); sehr gut gepflegt | Fehler in Vorlagen erst zur Laufzeit (weniger Typsicherheit als askama) |
| **maud** (0.27.0) **+ htmx** | HTML als Rust-Makro, voll typisiert | Letzter Release 02/2025; HTML im Rust-Code ist für Gestaltung und Übersetzung unhandlich |
| **askama + Datastar** (Rust-SDK `datastar` 0.4.2, aktiv) | Server-Sent Events als Grundprinzip: passt genau zum gestreamten Assistenten; kleine Signale im Browser | Jung, kleine Gemeinschaft; npm-Paket veraltet (Verteilung über CDN/GitHub ▲); wenig Vorbild-Code für Agenten |
| **+ Alpine.js** (3.17.5) als Ergänzung | Kleiner Client-Zustand (Aufklappen, Zähler) ohne Build | Noch ein Ansatz; 1 eingetragener Maintainer |

### Stil S4: Rust im Browser (WebAssembly)

| Kandidat (Version) | Vorteile | Nachteile |
|---|---|---|
| **Leptos** (0.8.23) mit SSR im axum-Prozess und **Inseln** | Eine Sprache und durchgehende Typen ohne Generator; Server rendert (G1), nur Inseln laden WASM; Serverfunktionen | Vor 1.0 (Brüche); zwei Übersetzungsziele (Server und WASM) verlängern Builds deutlich ▲; WASM-Inseln größer als JS ▲; wenig Vorbild-Code für Agenten; Service Worker trotzdem JS |
| **Dioxus** (0.7.10) Fullstack | Wie Leptos, zusätzlich Desktop und Mobil | Gleiche Nachteile; Fokus eher auf Apps außerhalb des Browsers |
| **Yew** (0.23.0) | Älteste Rust-UI-Bibliothek | Nur Client-Rendering, keine Inseln; seltene Releases |

### Stil S5: Mischform (Server-Rendering plus Inseln aus einem JS-Framework)

Seiten in Rust (S3), die drei interaktiven Stellen als Inseln (z. B. Svelte oder Preact als Custom Element, mit generierten TS-Typen).

| Vorteile | Nachteile |
|---|---|
| Jede Stelle bekommt das passende Werkzeug; Gastseite und Listen ohne Client-Code | Zwei Darstellungswelten, Übersetzungen in beiden; Grenzen zwischen Seite und Insel (Zustand, Fokus) müssen sauber gezogen werden |

## 4. Shortlist

| Kandidat | Stil | Warum in die Shortlist |
|---|---|---|
| **Svelte 5 / SvelteKit (statisch)** | S1 | Technisch stärkste SPA für dieses Profil: kleinste Bundles ▲, Barrierefreiheits-Prüfung im Compiler, Vorrendern statischer Seiten. Vertritt die SPA gegen die übrigen Stile. |
| **askama + htmx** (Alpine bei Bedarf) | S3 | Vertritt „Server zuerst“: beste Gastseite, Barrierefreiheit durch den Browser, ein Übersetzungskatalog. Prüft, ob Assistent und Stapel-Vorschau ohne Framework gut gehen. |
| **Leptos mit SSR und Inseln** | S4 | Die „saubere“ Ein-Sprachen-Antwort: Server-Rendering und Inseln mit Rust-Typen. Prüft, ob Build-Zeit, WASM-Größe und Agentenfähigkeit tragen. |

Nicht in der Shortlist: React, Vue, Preact, Solid, Angular (gleicher Stil wie Svelte, technisch für dieses Profil nicht besser); S2 (bringt ohne Node gegenüber S1 kaum etwas); minijinja, maud, Datastar (Varianten von S3, können nach dem Spike nachgezogen werden); S5 (Entscheidung erst sinnvoll, wenn S1 und S3 gemessen sind).

## 5. Spike-Plan F-1 (analog E-002)

**Grundlage:** das Rust-Backend aus dem E-002-Spike in der VM, vorab ergänzt um Rückmeldungen, Gastlinks mit Gast-Sitzung (E-008, T2-B), eine Assistent-Attrappe (Zwischenstände per SSE, Stapel mit Vorschau und Beleg nach ADR-005/006, ohne echte KI) und den Endpunkt für den VAPID-Schlüssel. Diese Basis wird **vor** den Kandidaten gebaut und mit einer API-Abnahme geprüft. Alle Kandidaten starten von derselben Basis; S3 und S4 rendern im selben axum-Prozess, S1 ruft die API.

**Umfang (Phase 1):**
1. **Gastseite:** Link öffnen, Termin sehen, Name, Ja/Vielleicht/Nein, speichern, Rückkehr-Link sehen; ≤ 3 Interaktionen.
2. **Konto:** Anmeldung über Keycloak, Terminliste des Teams, Termin anlegen (Validierungsfehler aus Fehlercodes), Termin absagen mit Vorschau und Freigabe.
3. **Assistent-Dialog:** Nachricht senden, Zwischenstände live, Stapel-Vorschau, Freigabe, Ergebnis.
4. **Mehrsprachigkeit:** DE/EN mit Plural („1 Zusage“, „3 Zusagen“) und Datum in der Zeitzone des Termins; Gäste nach Browsersprache.
5. **PWA:** Manifest, Service Worker mit Push-Empfang, Push-Abo anlegen.
6. **Barrierefreiheit:** Festlegungen aus T8 der gemeinsamen Analyse (Fokus und Ansage bei Seitenwechsel, Statusmeldungen, Radiogruppe, Mindestgröße der Berührungsflächen).

**Phase 2 (neue Funktion):** Terminfindung: Vorschläge als Raster, abstimmen, Auswertung. Gemessen wird der Aufwand.

**Abnahme (von mir vorab gebaut, für alle gleich):** Playwright-Tests, die die Oberfläche **nur über zugängliche Rollen und Beschriftungen** ansprechen (`getByRole`, `getByLabel`). Damit prüft jeder Test zugleich, ob die Oberfläche zugänglich ausgezeichnet ist. Dazu axe-core ohne Verstöße der Stufe AA, beide Sprachen.

**Messgrößen (Entwurf):**

| ID | Messgröße |
|---|---|
| MF-1 | Übertragene Bytes der Gastseite bis zur bedienbaren Seite (komprimiert) |
| MF-2 | Lighthouse (Mobil, gedrosselt): LCP und Total Blocking Time für Gastseite und Terminliste |
| MF-3 | Interaktionen bis zur gespeicherten Antwort (Gast) |
| MF-4 | Gesamtgröße der ausgelieferten Oberfläche (JS, CSS, WASM) |
| MF-5 | Zusätzliche Abhängigkeiten (npm Produktion und Entwicklung, Crates) |
| MF-6 | Bauzeit (voll, inkrementell) und Rückkopplung bei einer Textänderung in einer Seite |
| MF-7 | axe-Verstöße (Ziel 0) |
| MF-8 | Zeit bis Phase 1, Korrekturschleifen |
| MF-9 | Phase 2: berührte Dateien, Zeit |
| MF-10 | Zusätzlicher Speicher des Web-Prozesses unter Last |
| MF-11 | Eigenbau-Anteil der Oberfläche |
| QF-1 bis QF-3 | Bewertung durch den Product Owner: Verständlichkeit des Codes, Struktur, Eindruck auf dem eigenen Smartphone |

**Ablauf:** wie E-002 (VM, Benutzer `agent`, Netzsperre, Zeitbox, Abnahme und Messung unabhängig vom Agenten). Vorbereitung: Basis-Erweiterung, Abnahmesuite, Messskripte, Briefing, Validierung der Suite gegen eine Referenzoberfläche.

## Fragen an den Product Owner

1. Shortlist Svelte, askama + htmx, Leptos einverstanden, oder soll ein Kandidat dazu (z. B. Datastar statt htmx, oder S5 als vierter)?
2. Messgrößen und ihre Gewichtung: Soll die Gewichtung wie in E-002 aus ADR-001 abgeleitet werden?
3. Modell und Ablauf: Opus oder Sonnet, parallel oder nacheinander (in E-002 war das Nutzungslimit nach 7 Minuten erreicht)? Ist Claude Code in der VM noch angemeldet?
4. Die Basis-Erweiterung (Gäste, Rückmeldungen, Assistent-Attrappe) baue ich vorab selbst oder lasse sie von einem Agenten in der VM bauen?
