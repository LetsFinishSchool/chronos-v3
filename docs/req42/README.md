---
title: req42 – Anforderungen
status: entwurf
---

# req42

Anforderungen nach [req42](https://www.req42.de/) mit den 12 Artefakten. Jede Entität hat eine eigene Datei mit Frontmatter (`id`, `title`, `status`, `typ`, `quellen`, `verknuepft`); Dateiname `<ID>-<kebab-titel>.md`. Nur `status: freigegeben` gilt, alles andere ist Entwurf. Unsicheres ist mit **(?)** markiert; Festlegungen, die nur ein Mensch treffen kann, stehen gebündelt in [RA-008](12-risiken-annahmen/RA-008-offene-fragen.md). Je Ordner beschreibt `00-kapitelbeschreibung.md` (offizielle Vorlage, unverändert) den Zweck.

| Nr. | Verzeichnis | Inhalt | ID-Schema |
|---|---|---|---|
| 1 | [01-ziele/](01-ziele/README.md) | Ziele | `Z-nnn` |
| 2 | [02-stakeholder/](02-stakeholder/README.md) | Stakeholder | `SH-nnn` |
| 3 | [03-scope/](03-scope/README.md) | Scope-Abgrenzung | `SC-nnn` |
| 4 | [04-product-backlog/](04-product-backlog/README.md) | Features und Anforderungen mit Akzeptanzkriterien | `F-nnn`, `FA-nnn` |
| 5 | [05-modelle/](05-modelle/README.md) | Modelle | `M-nnn` |
| 6 | [06-qualitaet/](06-qualitaet/README.md) | Qualitätsanforderungen | `QA-nnn` |
| 7 | [07-randbedingungen/](07-randbedingungen/README.md) | Randbedingungen | `RB-nnn` |
| 8 | [08-terminologie/](08-terminologie/glossar.md) | Glossar | – |
| 9 | [09-betriebsmittel-personal/](09-betriebsmittel-personal/README.md) | Betriebsmittel und Personal | `BM-nnn` |
| 10 | [10-teamstruktur/](10-teamstruktur/README.md) | Teamstruktur | `TS-nnn` |
| 11 | [11-roadmaps/](11-roadmaps/README.md) | Roadmap | `RM-nnn` |
| 12 | [12-risiken-annahmen/](12-risiken-annahmen/README.md) | Risiken und Annahmen | `RA-nnn` |

**Neuanfang (2026-11-20):** req42 wurde für chronos-v3 neu geschrieben. Die Entitäten aus chronos-root (alte Nummerierung) sind nur in der Git-Historie; die IDs dieses req42 beginnen neu und sind ab jetzt stabil (nie umnummerieren, ersetzte Einträge `status: ersetzt`).

**Verknüpfung:** Anforderung → Feature → Ziel → Stakeholder. Nur in diese Richtung verlinken.

**Abgrenzung:** Dokumentiert ist, was Chronos leisten muss, nicht wie. Lösung und Entscheidungen: [arc42](../arc42/README.md) (noch zu erstellen).
