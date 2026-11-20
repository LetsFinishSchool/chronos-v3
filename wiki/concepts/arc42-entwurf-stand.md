---
title: arc42-Entwurf, Stand 2026-11-20
type: concept
sources:
  - docs/arc42/
  - docs/req42/
confidence: hoch
last-verified: 2026-11-20
---

# arc42-Entwurf, Stand 2026-11-20

Alle zwölf arc42-Kapitel sind als **Entwurf** befüllt, nur mit dem, was aus req42 ohne Entscheidung folgt. **Entscheidungen im Entwurf (Freigabe steht aus): ADR-001 Rangfolge der Qualitätsziele (Änderbarkeit > Bedienbarkeit > Ressourceneffizienz > Benachrichtigung > Nachvollziehbarkeit); ADR-002 Zerlegung: eine Codebasis, zwei Prozesse (Web und Worker), gemeinsame Datenbank; ADR-003 Datenbank: PostgreSQL in eigener Instanz (keine geteilte im Cluster).** E-002 (Sprache) in Bearbeitung: `docs/arc42/09-entscheidungen/E-002-sprachwahl-analyse.md`, Java/Kotlin und Python vom Product Owner ausgeschieden; Kandidaten TypeScript, Go, Rust, je ein Spike; Kriterien in `E-002-spike-kriterien.md` im Gespräch festgelegt (Entwurf): 8 h Wall-Clock je Agent, parallel und isoliert, amd64, lokales Keycloak, Messung und Abnahme unabhängig vom Agenten. Nächster Schritt: Vorbereitung V-1..V-6.

- **Vorgegeben (Kapitel 2/3/7):** k3s, Keycloak, S3-Backup, SMTP, Web Push, RFC 5545, Budget 1 vCPU/1 GiB, 10 €/Monat Zusatzkosten.
- **Zwingende Struktur (Kapitel 4/5):** UI und Assistent nutzen dieselbe Operationsschicht (RB-011); Fachbereiche kennen keine Kanäle; Ereignisse haben benannte Auslöser; Kosten laufen über eine erfassende Stelle.
- **Veränderlichkeit:** `docs/arc42/04-loesungsstrategie/02-veraenderlichkeit.md` listet Änderungsachsen (Kanäle, Terminarten, Funktionen, Sprachen, KI-Anbieter, Berechtigungsmodell …). Bei jeder neuen Anforderung prüfen, in welche Achse sie fällt.
- **Offen:** siehe `docs/arc42/09-entscheidungen/01-offene-entscheidungen.md`; ADR-001..003 am 2026-11-20 freigegeben, E-006, E-010..E-015 entschieden, E-007 und E-008 zurückgestellt.
- **Bausteine in Kapitel 5 sind Kandidaten**, kein Zuschnitt.

Nächster Schritt: E-000 bis E-003 gemeinsam mit dem Product Owner entscheiden, danach Kapitel 5 Ebene 2 und Kapitel 7 ausbauen.

Spike-Vorbereitung vollständig in `spikes/e-002/` (V-1..V-5 fertig und gegen eine Referenzattrappe validiert; V-6: Schlüssel bereit, technisches Kostenlimit per Schutz-Proxy eingebaut (Konsolenlimit als zweite Linie empfohlen)). Ablauf: `spikes/e-002/RUNBOOK.md`. Hinweis: rootless Docker (Mounts müssen lesbar sein), Messungen nacheinander ausführen.
