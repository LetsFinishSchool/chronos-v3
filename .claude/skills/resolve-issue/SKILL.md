---
name: resolve-issue
description: Setzt ein GitHub-Issue (meist ein Task) von Plan bis Pull Request um - Branch, Plan, Commit je Schritt, Review-Schleife mit Code-Reviewer-Subagent, PR. Verwenden bei "Setze Issue #N um", "Resolve #N" oder /goal mit Issue-Nummer.
argument-hint: "<Issue-Nummer>"
---

# resolve-issue

Setzt Issue `#$ARGUMENTS` autonom um. Ergebnis ist ein PR `Resolve #<N>: <Titel>`, den ein Mensch prüft und mergt. Nie selbst mergen.

Verbindliche Regeln stehen in `AGENTS.md` und `docs/req42/04-product-backlog/ticket-typen.md` (Task-DoD). Dieser Skill wiederholt sie nicht, sondern legt nur den Ablauf fest.

## 0. Voraussetzungen prüfen

1. Issue lesen (`gh issue view <N> --comments`), Typ-Label und Verweise (Eltern-Story, ADRs, `docs/`-Kapitel) beachten.
2. Ist es kein Task, ist `Ziel`, `Umsetzung` oder `Fertig, wenn` leer oder bleibt eine Rückfrage offen: **abbrechen**, die Lücke kurz benennen, nichts implementieren. Kein Raten.
3. Arbeitsbaum sauber und auf aktuellem `main`? Sonst `git fetch` und von `origin/main` abzweigen. Existiert `issue/<N>` schon, ihn weiterverwenden und `git log main..` lesen, statt neu zu beginnen.
4. Branch `issue/<N>` anlegen (Projektkonvention).

## 1. Wissen laden

Gemäß `AGENTS.md`: `wiki/index.md` lesen und passende Seiten laden, für Fachliches `docs/req42/` und `docs/arc42/`. Wiki-Aussagen mit altem `last-verified` gegen den Code prüfen.

## 2. Plan

Plan als nummerierte Checkliste in `.scratch/issue-<N>/plan.md` schreiben (Verzeichnis bei Bedarf anlegen). Format: `- [ ] 1. Kurzbeschreibung`. Regeln:

- Jeder Schritt ist klein, in sich lauffähig (baut, Tests grün) und ergibt **einen** Commit.
- Tests gehören zum Schritt, den sie absichern, nicht an das Ende.
- Letzter Schritt: Wiki nachziehen (Skill `chronos-wiki`).
- Jeder Punkt aus „Fertig, wenn“ muss einem Schritt zugeordnet sein. Was nicht zugeordnet werden kann, ist eine offene Frage, siehe Abbruchregel in Abschnitt 0.
- Nichts planen, was unter „Nicht Teil dieses Tasks“ fällt.

**Dateien in `.scratch/` werden niemals committet oder gestaged.** Das Verzeichnis steht in `.gitignore`; trotzdem nie mit `git add -f` hinzufügen. Dort liegen Plan und Arbeitsnotizen. Der Plan kommt später in die PR-Beschreibung.

## 3. Umsetzen

Schritte der Reihe nach abarbeiten. Nach jedem Schritt:

1. Prüfbefehle aus dem Abschnitt „Prüfung“ des Issues ausführen, mindestens soweit sie den Schritt betreffen. Erst committen, wenn grün. Fehlt der Abschnitt, gelten die CI-Prüfungen aus `.github/workflows/ci.yml` (`cargo fmt --all --check`, `cargo clippy --workspace --all-targets --locked -- -D warnings`, Tests).
2. Commit mit aussagekräftiger Nachricht (Was und Warum, auf Deutsch wie im Projekt üblich), Verweis `#<N>`. Nur Dateien dieses Schritts stagen, nie `git add -A` blind.
3. Schritt in `.scratch/issue-<N>/plan.md` abhaken (`- [x]`), mit Commit-Hash und, falls abweichend vom Plan, einer Zeile Begründung. Bei einer Plankorrektur den Plan anpassen, nicht stillschweigend abweichen. Beim Wiederaufnehmen (neue Session, bestehender Branch) zuerst `plan.md` lesen und beim ersten offenen Schritt weitermachen.

Leitplanken, die der Reviewer später ohnehin prüft:

- Nur ändern, was das Issue verlangt.
- `docs/` nie ändern. Widerspruch oder neue verbindliche Erkenntnis: `wiki/proposals/_vorlage.md`.
- Kommentare nur nach den drei Bedingungen aus `AGENTS.md`.
- Keine Geheimnisse; Migrationen nur vorwärts; Oberflächentexte übersetzbar (de/en).
- Schlägt ein Schritt nach zwei ernsthaften Versuchen weiter fehl: stoppen und berichten, nicht an Tests vorbeibauen oder sie abschwächen.

## 4. Review-Schleife

Wiederhole, **maximal 5 Runden**:

1. Starte einen **frischen** Code-Reviewer-Subagenten (Agent-Tool, `general-purpose`, jede Runde neu, damit er unvoreingenommen bleibt). Der Prompt enthält:
   - Issue-Nummer und den vollen Issue-Text (Ziel, Fertig-wenn, Nicht-Teil).
   - Auftrag: `git diff origin/main...HEAD` prüfen, nur lesen, nichts ändern.
   - Prüfmaßstab: Korrektheit und Fehlerfälle, Abdeckung jedes „Fertig, wenn“-Punkts durch Tests, Umfang (nichts Fremdes geändert), Task-DoD aus `ticket-typen.md`, Kommentarregeln und Projektkonventionen aus `AGENTS.md`, Sicherheit (Geheimnisse, SQL, Berechtigungen).
   - Ausgabe: nummerierte Findings mit Datei:Zeile, Schweregrad (`blocker`/`wichtig`/`nit`) und Begründung. Ohne Findings genau: `KEINE FINDINGS`.
   - **Keine** Informationen über frühere Runden, behobene oder abgelehnte Findings. Der Reviewer schaut jedes Mal frisch auf den Code.
   Alternativ oder ergänzend `/code-review high` auf dem Branch verwenden.
2. Findings einzeln bewerten:
   - **Berechtigt:** beheben, Prüfbefehle laufen lassen, **eigener Commit** (`Review: <Kurzbeschreibung>`).
   - **Nicht berechtigt** (Fehlalarm, außerhalb des Umfangs, widerspricht `docs/`): ablehnen und die Begründung in einer Zeile in `.scratch/issue-<N>/review.md` festhalten (Runde, Finding, Begründung). Nicht stillschweigend ignorieren.
   - Auch behobene Findings dort kurz protokollieren; daraus entsteht der Review-Abschnitt im PR.
3. Beendet ist die Schleife, wenn der Reviewer `KEINE FINDINGS` meldet **oder** alle gemeldeten Findings nur `nit` sind bzw. bereits in `review.md` mit Begründung abgelehnt wurden (der Agent gleicht das selbst ab, der Reviewer erfährt davon nichts). Nach Runde 5 ohne Ende: nicht weiter iterieren, offene Findings im PR benennen.

Bei jedem Behobenen Finding gilt wieder: Tests grün, bevor committet wird.

## 5. Abschluss und PR

1. Vollständige Prüfung einmal über alles (`fmt`, `clippy`, Tests, gegebenenfalls `cargo sqlx prepare --check`, `cargo deny check` wie in der CI). Rot: beheben, nicht pushen.
2. Wiki ist nachgezogen (`wiki/index.md`, `wiki/log.md`); gab es nichts zu lernen, Log-Eintrag „kein Wiki-Bedarf“.
3. `git push -u origin issue/<N>`.
4. PR gegen `main` mit `gh pr create`:
   - Titel: `Resolve #<N>: <Titel des Issues>`
   - Body beginnt mit `Closes #<N>`, danach: Zusammenfassung, der Plan mit Häkchen, Zuordnung „Fertig, wenn“ → Test/Beleg, Ergebnis der Review-Schleife (Runden, behobene Findings, abgelehnte Findings mit Begründung, ggf. offene Punkte), ausgeführte Prüfbefehle.
   - Zeilen für Attribution am Ende wie in der Session vorgegeben.
5. CI beobachten (`gh pr checks --watch`). Schlägt sie fehl: Ursache beheben, committen, pushen. Höchstens 3 Korrekturversuche, dann berichten.
6. Abschlussbericht an den Menschen: PR-Link, was umgesetzt wurde, was offen ist. Nicht mergen, Issue nicht selbst schließen.

## Abbruch und Rückfragen

Bei Unklarheit im Issue, Widerspruch zu `docs/` oder nötigem Eingriff außerhalb des Umfangs: anhalten, Frage klar formulieren, ggf. als Kommentar am Issue hinterlassen. Lieber früh stoppen als einen PR mit geratenen Annahmen öffnen.
