---
title: Image, Helm-Chart und Deployment auf staging
type: code
sources:
  - issue:#104
  - docs/arc42/09-entscheidungen/ADR-013-build-ci-lieferkette.md
  - docs/arc42/09-entscheidungen/ADR-011-migrationswerkzeug.md
  - docs/arc42/07-verteilung/01-verteilungssicht.md
  - Dockerfile
  - deploy/helm/chronos/
  - .github/workflows/ci.yml
confidence: mittel
last-verified: 2026-11-27
---

# Image, Helm-Chart und Deployment auf staging

- **Image:** `Dockerfile` mit einer Node-Stage für den Frontend-Build (`CHRONOS_FRONTEND_DIR` im Image gesetzt, siehe `code/frontend.md`) und `cargo-chef` (`0.1.78-rust-1.100.0-slim-trixie`, Rust muss zu `rust-toolchain.toml` passen), Laufzeit `gcr.io/distroless/cc-debian13:nonroot`, `ENTRYPOINT chronos`, Standard-Unterbefehl `serve`. `SQLX_OFFLINE=true` im Build. `.dockerignore` schließt `.env`/`.envrc` aus (Worktrees enthalten sie, sie dürfen in keine Schicht, RB-008). Kalter Build ca. 2 Minuten. Tags von `cargo-chef` vorher auf Docker Hub prüfen, es gibt nicht zu jeder Rust-Version alle Varianten.
- **Chart** `deploy/helm/chronos/`: `web.yaml` (Deployment, Service, Ingress), `worker.yaml`, `postgres.yaml` (StatefulSet, Service `chronos-postgres`, Init-Skript als ConfigMap), `migrate-job.yaml`. `image.tag` hat absichtlich keinen Standard (Commit-SHA von CI). `ingress.host` kommt aus `values-staging.yaml`.
- **Migrationsjob, Stolperstein:** Ein `pre-install`-Hook läuft *vor* den Ressourcen des Releases, also vor dem PostgreSQL-StatefulSet. Deshalb ist der Job beim Upgrade ein `pre-upgrade`-Hook (blockiert das Rollout, alte Version läuft weiter), bei der Erstinstallation eine normale Ressource (`chronos-migrate-install`; Helm wartet nur mit `--wait-for-jobs` darauf, Web/Worker warten auf das Schema). Abweichung vom Ticketwortlaut „pre-install/pre-upgrade“, Begründung als Kommentar in `migrate-job.yaml`.
- **Rollen:** Init-Skript des PostgreSQL-Containers (`/docker-entrypoint-initdb.d`, läuft nur bei leerem Datenverzeichnis) legt `chronos_migrate` und `chronos_app` mit Passwörtern aus dem Secret an, über `psql -v` und `:'var'` (kein Quoting-Problem bei Sonderzeichen; lokal mit `'`, `$`, Leerzeichen getestet). Spätere Passwortwechsel im Secret wirken **nicht** auf eine bestehende Datenbank.
- **Limits:** Summe 1 vCPU / 1 GiB je Umgebung: Web 400m/384Mi, Worker 200m/128Mi, PostgreSQL 400m/512Mi. Aufteilung vorläufig, bis der Lasttest sie belegt (Kapitel 7: „zu bestimmen“).
- **Startup-Probe** im Web: der Port öffnet erst nach dem Schema-Warten (bis 60 s), die Liveness-Probe allein würde den Pod dabei töten. Der Workflow bricht nur bei Pull Requests ältere Läufe ab, sonst bliebe ein abgebrochenes `helm upgrade` als `pending-upgrade` hängen. Limit-Spitzen beim Rolling Update und Migrationsjob liegen kurz über 1 vCPU/1 GiB; im PR-Messwert erwähnen.
- **Worker** hat keine Probes (kein HTTP-Port). `CHRONOS_ENV` ist nicht gesetzt (Standard Produktion, sicher; „staging“ ist kein gültiger Wert).
- **CI:** Jobs `chart` (lint und `template` im Install- und Upgrade-Modus), `image` (PR: nur bauen; `main`: push nach `ghcr.io/letsfinishschool/chronos-v3:<sha>`), `deploy` (nur Push auf `main`, Environment `staging`, `concurrency` ohne Abbruch, `helm upgrade --install --atomic --wait --wait-for-jobs --timeout 5m`). Actions auf Commit-Hash.
- **Prüfstand:** `kubeconform` war lokal nicht installiert (nicht installiert, Binary-Download wurde abgelehnt); nur `helm lint`/`helm template` geprüft. Rollout, Ingress, Gegenprobe und Leerlaufmesswert waren ohne Clusterzugang nicht prüfbar und stehen im PR als offen.
