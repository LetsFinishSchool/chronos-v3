---
title: Widerspruch zur Deployment-Form (Kapitel 7 gegen ADR-011): kustomize oder Helm
datum: 2026-11-24
betrifft: docs/arc42/07-verteilung/01-verteilungssicht.md, docs/arc42/09-entscheidungen/ADR-011-migrationswerkzeug.md
art: widerspruch
status: offen   # Teil „ein Image“ vom Product Owner am 2026-11-24 entschieden und in docs/ übernommen
---

## Beobachtung
- Kapitel 7 nennt Deployment über Manifeste im Repository, angewendet per CI mit kubectl/kustomize (PO 2026-11-20).
- ADR-011 (PO 2026-11-24) legt als Form des Migrationsjobs einen Helm-Hook (`pre-install`/`pre-upgrade`) fest und spricht von einem Helm-Chart.
- Erledigt: Die Frage „ein Image oder zwei“ hat der Product Owner am 2026-11-24 mit „ein Image mit Unterbefehlen“ entschieden; Kapitel 7 und ADR-002 sind angepasst.
- Betroffen: Ticket „Image, Helm/Manifeste und Deployment auf staging“ (#104).

## Vorschlag
Product Owner entscheidet: Helm mit Hook **oder** kustomize mit Job. ADR-011 verlangt den Ablauf „Job vor Rollout“; mit kustomize ginge das nur über eine CI-Reihenfolge (Job anwenden, auf Abschluss warten, dann Deployments). Die jeweils nicht gewählte Aussage wird in Kapitel 7 oder ADR-011 ersetzt (nicht überschrieben, siehe `docs/README.md`).

## Wirkung
Nur #104 wird blockiert; #99 bis #103 sind unabhängig. Kapitel 7 oder ADR-011 brauchen danach eine Korrektur.

## Entscheidung (Mensch)
