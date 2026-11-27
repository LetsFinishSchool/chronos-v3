---
title: Frontend-Gerüst (Svelte, statischer Build, Auslieferung, Tests)
type: code
sources:
  - issue:#103
  - issue:#116
  - frontend/playwright.config.ts
  - frontend/e2e/support/axe.ts
  - frontend/scripts/bundle-size.mjs
  - .github/workflows/ci.yml
  - docs/arc42/09-entscheidungen/ADR-007-frontend-spa-svelte.md
  - frontend/package.json
  - frontend/app/vite.config.ts
  - crates/web/src/lib.rs
  - crates/chronos/src/main.rs
  - Dockerfile
confidence: hoch
last-verified: 2026-11-27
---

# Frontend-Gerüst (#103) und Tests (#116)

## Aufbau
- `frontend/` ist npm-Workspace-Wurzel (`app`, `packages/*`), Anwendung in `frontend/app/`. Exakte Versionen (`.npmrc` `save-exact=true`), `package-lock.json` im Repo, Node 22.
- SvelteKit nur für Routing und `adapter-static` (`fallback: "index.html"`); `ssr = false`, `prerender = false` in `+layout.ts`. Build nach `frontend/app/build`.
- Texte nur über `t(key)` aus `src/lib/i18n.ts` (V-3); #47 ersetzt diese Datei durch den Fluent-Katalog.
- Ladehülle (Wireframe „Laden“, Text bewusst nicht aus `t()`, siehe Wireframe-Hinweis) steht statisch in `src/app.html`; `+layout.svelte` entfernt sie beim Mounten, sonst stünde sie als zweites `h1` neben der Seite (Svelte räumt das Ziel nicht).

## Auslieferung
- `chronos_web::router(frontend_dir)`: `/healthz`, `/api` und `/api/…` (alle Methoden) → 404, alles andere `ServeDir` mit Fallback `index.html` (Status 200, GET und HEAD). Assets (`/_app/…` und bekannte Dateiendungen) ohne Treffer liefern 404 statt Shell, sonst bekäme ein alter Browser-Cache HTML als Skript; Seitenpfade mit Punkt (`/x/ab.cd`) bleiben Shell. `Cache-Control`: `no-cache` für Shell und sonstige Antworten, `immutable` für `/_app/immutable/…`.
- `chronos serve` liest `CHRONOS_FRONTEND_DIR` (Standard `frontend/app/build`, relativ zum Arbeitsverzeichnis) und prüft, dass `index.html` existiert; sonst `Failure::Config`, Exit 1, **vor** dem Datenbankzugriff. Tests, die `serve` starten, setzen die Variable auf `crates/chronos/tests/fixtures/frontend`.

## Image
- `Dockerfile` hat eine Stage `frontend` (`node:22.21.1-trixie-slim`, `npm ci`, `npm run build`); der Build liegt im Image unter `/usr/local/share/chronos/frontend`, `CHRONOS_FRONTEND_DIR` ist per `ENV` darauf gesetzt. Nötig, weil das distroless-Image keinen sinnvollen Arbeitsordner für den relativen Standardpfad hat und `serve` sonst nicht startet. #104 hatte das Frontend noch nicht enthalten.
- `.dockerignore` hält `node_modules`, Build und `.svelte-kit` aus dem Kontext. Die Node-Version steht in `frontend/.node-version` und im `FROM` und muss gemeinsam angehoben werden.

## Router-Wrapper (#116)
- `src/lib/router/Router.svelte` steht im Wurzel-Layout: nach jedem `afterNavigate` (außer dem ersten Laden, `type === "enter"`) Fokus auf die `h1` (`tabindex="-1"` wird gesetzt) und `document.title` in eine Live-Region (`role="status"`, `aria-live="polite"`). Seiten brauchen nur eine `h1` und einen `<title>`. Wegen `#lib/*.svelte` in `imports` von `app/package.json` importierbar.

## Tests (#116)
- `frontend/e2e/` mit `@playwright/test` (nur Chromium), Konfiguration `frontend/playwright.config.ts`. `webServer` startet `cargo run -p chronos -- serve` auf `127.0.0.1:4318` mit `CHRONOS_FRONTEND_DIR=frontend/app/build`; nötig sind gebauter Frontend-Build, migrierte Datenbank und `DATABASE_URL_APP` in der Umgebung. Lokal: `npm --prefix frontend run test:e2e`. Die Config nutzt `__dirname`, da `frontend/package.json` kein ESM ist (`import.meta` scheitert).
- Tests sprechen die Seite nur über `getByRole`/`getByLabel` an (V-5). `e2e/support/axe.ts`: `expectNoA11yViolations(page)` (WCAG 2.2 AA, Tags `wcag2a`…`wcag22aa`), Meldung mit Regel, Wirkung, Elementen. Gegenprobe in `a11y.spec.ts` fügt ein Bild ohne `alt` per `page.evaluate` ein. `navigation.spec.ts` prüft Fokus und Live-Region; ohne `<Router />` im Layout schlägt er fehl (lokal geprüft).
- `scripts/bundle-size.mjs` (`npm run bundle-size`): gzip-Größe von JS/CSS je Datei und gesamt, auch in `$GITHUB_STEP_SUMMARY`; kein Budget (ADR-007, folgt mit Messwerten). Stand: etwa 36 KB gesamt.
- CI-Job `frontend` in `ci.yml`: `npm ci`, `npm audit --audit-level=high --omit=dev` (`continue-on-error`, nur Hinweis), Build, Bundle-Größe, Playwright-Installation, Migration, Tests, Bericht als Artefakt bei Fehler. Nicht in `needs` von `deploy`.
- Lokaler Lauf im Agenten-Setup: Postgres über Socket-Workaround (siehe `code/datenbank-und-migrationen.md`), `DATABASE_URL_APP=…?host=/tmp/…` und `SQLX_OFFLINE=true` exportieren.

## Stolpersteine
- **SvelteKit 3 statt 2:** Das Ticket nannte „kit 2“; alle 2.x-Versionen haben offene High-Advisories in `npm audit` (Fix nur in 3.x). Deshalb `@sveltejs/kit` 3.4.1, `adapter-static` 4.0.1, `typescript` 6.0.3 (Kit 3 verlangt TS 6), `vite` 8. Kit 3: keine `svelte.config.js` mehr (Konfiguration im `sveltekit(...)`-Plugin in `vite.config.ts`), `$lib` entfernt (Ersatz `#lib/…` über `imports` in `app/package.json`), `tsconfig` erbt von `$app/tsconfig`.
- `frontend/app/node_modules/` entsteht (von Kit erzeugtes `$app`) und ist gitignoriert.
- Postgres-Tests im Agenten-Setup: siehe `code/datenbank-und-migrationen.md` (Socket-Workaround); die `query!`-Makros brauchen eine migrierte Datenbank (`chronos migrate`) oder `SQLX_OFFLINE=true`.
