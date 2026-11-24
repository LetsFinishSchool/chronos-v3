---
title: req42-Backlog (FA/F) und Überführung in GitHub-Issues
type: concept
sources:
  - docs/req42/04-product-backlog/README.md
  - docs/req42/04-product-backlog/ticket-typen.md
  - issue:#1
confidence: mittel
last-verified: 2026-11-24
---

# req42-Backlog und GitHub-Issues

**Vorher (bis 2026-11-24):** `F-nnn` (Feature: Story-Satz, Umfang, Entscheidungen) und `FA-nnn` (Anforderung: 2 bis 5 Akzeptanzkriterien) waren 1:1 gepaart, beide auf Feature-Granularität, obwohl `ticket-typen.md` `FA` der Story zuordnete. Das Template von req42 kennt nur Epics, Features und Stories.

**Jetzt:** Die Dateien sind gelöscht (Git-Historie vor dem Commit dieser Überführung). Der Backlog liegt in 91 Issues (7 Epics `RM-nnn`, 18 Features, 55 Stories, 11 Tasks, 1 Option), verknüpft über Sub-Issues. Die Zuordnung früherer Kennungen steht in `docs/req42/04-product-backlog/README.md`; Stories nennen ihre Herkunft („ehemals FA-nnn, Kriterium n“).

**Was bei der Überführung angepasst wurde (und warum)**
- F-005 und F-008 sind je auf zwei Tickets geteilt (ein Ticket hat nur ein Elternticket): „zeitweise“ in RM-003, Messenger als Option.
- F-013 ist eine einzelne Story direkt am Epic RM-001; F-012 sind Tasks unter RM-001 (Abgleich der Datensatzzahlen als Erfolgskriterium des Epics).
- Querschnittliches (Soft-Delete, Änderungsverlauf, Operationsschicht, KI-Gateway, i18n, Backup) wurde als Task unter dem passenden Feature oder Epic angelegt.
- QA- und RB-Anforderungen, die nur einzelne Stories betreffen, sind deren Akzeptanzkriterien; die übrigen stehen in der Definition of Done von `ticket-typen.md` (Vorschlag angenommen und übernommen).
- `needs-po` ist aus `ticket-typen.md` und den Issue-Vorlagen entfernt.

**Stolpersteine**
- Tickets enthalten Links auf `docs/` über `blob/main`; sie sind nur gültig, solange die Dateinamen stabil bleiben.
- Plain-Text-Kennungen `F-nnn`/`FA-nnn` in arc42 bleiben stehen und lösen sich über die Tabelle in Kapitel 4 auf; nur Links wurden auf Issues umgestellt.
- `area:*`-Labels und Java als Sprache sind aus `ticket-typen.md` und den Vorlagen entfernt (Backend ist Rust, ADR-004); Prüfbefehle legt die Entwicklung je Baustein fest.
- Anlegen per Skript: `gh api` mit Sub-Issues-Endpunkt braucht die Issue-**ID** (nicht die Nummer); bei ~90 Anlagen 2 s Pause je Aufruf wegen Rate-Limit.
