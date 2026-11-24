---
title: KI-Anbieter nur mit EU-Datenstandort statt „Start mit Claude“
datum: 2026-11-23
betrifft: docs/req42/04-product-backlog/features/F-015-ki-assistent.md, docs/req42/03-scope/SC-001-systemkontext.md
art: widerspruch
status: angenommen   # Mensch setzt: angenommen | abgelehnt | zurückgestellt
---

## Beobachtung
ADR-006 (freigegeben vom Product Owner am 2026-11-23) lässt nur KI-Anbieter mit garantiertem europäischem Datenstandort zu, angebunden über das LiteLLM-Gateway. Die Anthropic-API bietet keinen EU-Standort (`inference_geo` nur `global`/`us`, Claude-Dokumentation 2026-11-23). req42 sagt an zwei Stellen „Start mit Claude“:
- `docs/req42/04-product-backlog/features/F-015-ki-assistent.md`, Abschnitt „Entscheidung“
- `docs/req42/03-scope/SC-001-systemkontext.md`, Tabelle, Zeile „KI-Anbieter“

`RA-008` (Runde 6) bleibt als Protokoll der damaligen Entscheidung unverändert.

## Vorschlag

**F-015, Abschnitt „Entscheidung“**

Alt:
> - Anbieterneutrale Schnittstelle, Start mit Claude; konkretes Modell in arc42.

Neu:
> - Anbieterneutrale Schnittstelle über ein KI-Gateway; nur Anbieter mit garantiertem europäischem Datenstandort; konkretes Modell nach Prüfkatalog ([ADR-006](../../../arc42/09-entscheidungen/ADR-006-ki-anbindung.md)).

**F-015, Abschnitt „Offen“**

Alt:
> - Datenschutz beim KI-Anbieter im Detail (AV-Vertrag, Datenumfang)

Neu:
> - AV-Vertrag und Aufbewahrung beim gewählten EU-Anbieter prüfen (ADR-006, Bedingung 7)

**SC-001, Tabelle, Zeile „KI-Anbieter“**

Alt:
> | KI-Anbieter | System | Dialog und Operationsaufrufe des Assistenten ([F-015](…)); anbieterneutral, Start mit Claude; erhält personenbezogene Daten ([RA-010](…)) | Gesprächsinhalte, Operationsaufrufe |

Neu:
> | KI-Anbieter | System | Dialog und Operationsaufrufe des Assistenten ([F-015](…)); anbieterneutral über das KI-Gateway des Betreibers, nur Anbieter mit EU-Datenstandort; erhält personenbezogene Daten ([RA-010](…)) | Gesprächsinhalte, Operationsaufrufe |

**SC-001, neue Tabellenzeile und Kante im Diagramm**

> | KI-Gateway (LiteLLM) | System, vom Betreiber betrieben | Leitet Anfragen des Assistenten an den zulässigen KI-Anbieter weiter, liefert Kosten je Aufruf | Gesprächsinhalte (durchgeleitet, nicht gespeichert), Kosten |

Diagramm: `C -- Dialog, Operationsaufrufe --> GW[KI-Gateway] --> AI[KI-Anbieter, EU]` statt `C -- … --> AI`.

## Wirkung
- req42 stimmt wieder mit ADR-006 überein; arc42 (K-006, Kapitel 3, Veränderlichkeit) ist bereits mit ADR-006 angepasst.
- Die Datenschutzerklärung nennt den EU-Anbieter und das Gateway statt Anthropic.
- Kein Einfluss auf Code, der noch nicht existiert.

## Entscheidung (Mensch)
Angenommen vom Product Owner am 2026-11-23 und in F-015 und SC-001 übernommen.
