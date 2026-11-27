# Frontend

Svelte 5 mit SvelteKit als statischer Build (ADR-007). Die Anwendung liegt in `app/`, `frontend/` ist die npm-Workspace-Wurzel.

```sh
npm --prefix frontend ci
npm --prefix frontend run build   # Ausgabe: frontend/app/build
npm --prefix frontend run check   # svelte-check
cargo run -p chronos -- serve     # liefert den Build aus (CHRONOS_FRONTEND_DIR, Standard frontend/app/build)
```
