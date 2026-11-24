# docs/ – gemeinsam gepflegte Wahrheit

Dieser Bereich enthält die **verbindlichen** Dokumente zu Chronos. Er gehört Menschen und Agenten gemeinsam, aber
**jede Änderung braucht eine menschliche Freigabe** (Review durch die Code-Owner, siehe `.github/CODEOWNERS`).

| Dokument | Frage, die es beantwortet |
|---|---|
| [vision/product-vision.md](vision/product-vision.md) | Wofür gibt es Chronos, für wen, woran messen wir Erfolg? |
| [req42/](req42/README.md) | Was muss das System leisten (Ziele, Stakeholder, Anforderungen, Qualitätsziele)? |
| [arc42/](arc42/README.md) | Wie ist das System gebaut und warum (Kontext, Bausteine, Laufzeit, Entscheidungen)? |

## Regeln

1. **Menschliche Freigabe.** PRs, die `docs/` ändern, werden nur von einem Menschen gemergt. Agenten dürfen Änderungen
   *vorschlagen* (PR oder Vorschlagsdatei, siehe [AGENTS.md](../AGENTS.md)), aber nie selbst freigeben oder automatisch mergen.
2. **Nur Verbindliches.** Was hier steht, gilt. Beobachtungen, Vermutungen und Gelerntes gehören nicht hierher.
3. **Änderungen sind Entscheidungen.** Jeder PR nennt Anlass (Ticket/Gespräch) und Wirkung. Ändert sich eine
   Architekturentscheidung, wird sie in `arc42/09-entscheidungen/` ersetzt, nicht stillschweigend überschrieben.
4. **Sprache.** Deutsch, wie die Oberfläche. Code-Namen bleiben englisch (Zuordnung: Glossar).
5. **Status im Frontmatter.** `status: entwurf | freigegeben`, `freigegeben-am`, `freigegeben-von`. Entwürfe gelten noch nicht.
6. **Eine Datei, ein Thema.** Kurz halten; Details gehören in Code und Tests, nicht hierher.
7. **Keine Verweise auf das Wiki.** `docs/` ist die Quelle der Wahrheit und steht für sich allein. Es enthält keine Links, Pfade oder Quellenangaben auf `wiki/`; Wissen, auf das `docs/` angewiesen ist, steht in `docs/`. Die Abhängigkeit läuft nur in eine Richtung: das Wiki darf auf `docs/` verweisen, nie umgekehrt.

## Wie ein Agent hier arbeitet

Agenten lesen `docs/` als Eingabe und ändern es nie ohne menschliche Freigabe. Den Ablauf (Widersprüche melden, Vorschläge) regelt [AGENTS.md](../AGENTS.md).
