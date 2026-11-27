---
title: Frontend-Gerüst (Svelte, statischer Build, Auslieferung)
type: code
sources:
  - issue:#103
  - docs/arc42/09-entscheidungen/ADR-007-frontend-spa-svelte.md
  - frontend/package.json
  - frontend/app/vite.config.ts
  - crates/web/src/lib.rs
  - crates/chronos/src/main.rs
confidence: hoch
last-verified: 2026-11-27
---

# Frontend-Gerüst (#103)

## Aufbau
- `frontend/` ist npm-Workspace-Wurzel (`app`, `packages/*`), Anwendung in `frontend/app/`. Exakte Versionen (`.npmrc` `save-exact=true`), `package-lock.json` im Repo, Node 22.
- SvelteKit nur für Routing und `adapter-static` (`fallback: "index.html"`); `ssr = false`, `prerender = false` in `+layout.ts`. Build nach `frontend/app/build`.
- Texte nur über `t(key)` aus `src/lib/i18n.ts` (V-3); #47 ersetzt diese Datei durch den Fluent-Katalog.
- Ladehülle (Wireframe „Laden“) steht statisch in `src/app.html`; `+layout.svelte` entfernt sie beim Mounten, sonst stünde sie als zweites `h1` neben der Seite (Svelte räumt das Ziel nicht).

## Auslieferung
- `chronos_web::router(frontend_dir)`: `/healthz`, `/api` und `/api/…` (alle Methoden) → 404, alles andere `ServeDir` mit Fallback `index.html` (Status 200, GET und HEAD).
- `chronos serve` liest `CHRONOS_FRONTEND_DIR` (Standard `frontend/app/build`, relativ zum Arbeitsverzeichnis) und prüft, dass `index.html` existiert; sonst `Failure::Config`, Exit 1, **vor** dem Datenbankzugriff. Tests, die `serve` starten, setzen die Variable auf `crates/chronos/tests/fixtures/frontend`.

## Stolpersteine
- **SvelteKit 3 statt 2:** Das Ticket nannte „kit 2“; alle 2.x-Versionen haben offene High-Advisories in `npm audit` (Fix nur in 3.x). Deshalb `@sveltejs/kit` 3.4.1, `adapter-static` 4.0.1, `typescript` 6.0.3 (Kit 3 verlangt TS 6), `vite` 8. Kit 3: keine `svelte.config.js` mehr (Konfiguration im `sveltekit(...)`-Plugin in `vite.config.ts`), `$lib` entfernt (Ersatz `#lib/…` über `imports` in `app/package.json`), `tsconfig` erbt von `$app/tsconfig`.
- `frontend/app/node_modules/` entsteht (von Kit erzeugtes `$app`) und ist gitignoriert.
- Postgres-Tests im Agenten-Setup: siehe `code/datenbank-und-migrationen.md` (Socket-Workaround); die `query!`-Makros brauchen eine migrierte Datenbank (`chronos migrate`) oder `SQLX_OFFLINE=true`.
