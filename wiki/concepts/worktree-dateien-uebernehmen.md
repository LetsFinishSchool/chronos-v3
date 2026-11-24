---
title: Worktrees: gitignorierte Dateien (.env, .envrc) übernehmen
type: concept
sources:
  - session:2026-11-24 (Analyse herdr 0.9.5 und Hook-Test)
  - .githooks/post-checkout
  - .worktreekeep
confidence: hoch
last-verified: 2026-11-24
---

# Worktrees: `.env` und `.envrc` übernehmen

**Problem:** `git worktree add` legt nur getrackte Dateien an. `.env` und `.envrc` sind gitignoriert, fehlen also in jedem neuen Worktree. herdr (0.9.5, `herdr worktree create`) kennt weder `.worktreekeep` noch `.worktreeinclude` und kopiert nichts.

**Lösung:** Der Git-Hook `.githooks/post-checkout` kopiert beim Anlegen eines Worktrees alle in `.worktreekeep` (eine Datei pro Zeile, `#` = Kommentar) gelisteten Dateien aus dem Haupt-Worktree. Er gilt für jedes Werkzeug (herdr, Git direkt, Agenten).

**Aktivierung:** einmalig pro Klon `git config core.hooksPath .githooks`.

**Verhalten:**
- Läuft nur direkt nach `git worktree add` (alter Stand = Null-Hash) und nie im Haupt-Worktree.
- Überschreibt nie bestehende Dateien; Rechte bleiben erhalten (`cp -p`, `.env` ist `600`).
- Lehnt absolute Pfade und `..` ab.
- Liest die Liste aus dem **Haupt-Worktree** (nicht aus dem neuen), sonst gilt bei uncommitteten Änderungen an `.worktreekeep` die alte Fassung.
- Danach in jedem Worktree einmal `direnv allow`.

**Stolperstein:** Der Hook `.claude/hooks/block-env-read.sh` blockiert Agenten-Bash-Befehle, die `.env`/`.envrc` nennen. Prüfungen dazu macht die Person selbst (`!`-Präfix).
