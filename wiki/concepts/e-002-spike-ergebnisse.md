---
title: E-002 Spike: Lehren für Agentenläufe
type: concept
sources:
  - docs/arc42/09-entscheidungen/ADR-004-sprache-und-laufzeit.md
  - docs/arc42/09-entscheidungen/E-002-spike-kriterien.md
  - spikes/e-002/ (lokal, Berichte und Ergebnisse sind git-ignoriert)
confidence: mittel
last-verified: 2026-11-24
---

# E-002 Spike-Ergebnisse: Lehren

Ergebnisse, Messwerte, Punkte, Python-Befunde und Entscheidung (Rust): [ADR-004](../../docs/arc42/09-entscheidungen/ADR-004-sprache-und-laufzeit.md). Rohdaten im Branch `spikes/e-002-ergebnisse`. Hier nur, was für künftige Agentenläufe gilt.

**Lehren für künftige Spikes und Agentenläufe**
- Das Nutzungslimit des Kontos ist ein Fremdlimit der Agenten: Drei parallele Opus-Agenten erreichten es in 7 Minuten. Vor dem Start Limit und Modell klären, sonst Läufe nacheinander oder mit Sonnet.
- Die VM-Festplatte (31 GB) füllte sich durch Rust-`target`-Verzeichnisse (4 bis 5 GB je Klon) und Docker-Images. Vor Messungen `df` prüfen, Docker-Cache und Archive entfernen.
- Eine Aufgabenbeschreibung darf Endpunkte nicht nur in Testseiten voraussetzen (V-1 ohne `GET /api/v1/push/vapid-public-key`): Nur ein Agent baute ihn, der manuelle Test K3 scheiterte bei den anderen scheinbar. Alle Verträge gehören in die Spezifikation.
- Browser sperren Port 10080 (und weitere „unsichere“ Ports): lokale Tunnelports außerhalb dieser Liste wählen.
- Docker-Healthchecks von Images (Mailpit prüft Port 8025) schlagen bei verschobenen Ports fehl; `compose up --wait` bricht dann ab, obwohl der Dienst läuft.
- Abhängigkeitszahlen sind nur vergleichbar, wenn dieselbe Definition gilt (Produktions-Build, ohne Entwicklungsabhängigkeiten, bereinigt); die erste Messung war nicht vergleichbar.
- Agenten messen sich selbst zu optimistisch („Phase 1 in 12 min“): Abnahme und Messung immer unabhängig und aus den Originalskripten, nicht aus Arbeitskopien.
- Eine KI-Operation (`ai.ask`) hielt im Python-Spike eine DB-Transaktion während des Modellaufrufs offen: Transaktionen nie über externe Aufrufe halten.

**Lehren aus dem Python-Lauf:** Messwerkzeuge laufen nur fair, wenn die Werkzeuge der Sprache lokal installiert sind (uv im Container verfälschte M-7 und M-12 um den Docker-Start). Startskripte für Agenten (Phase 2) gehören ins Repository, nicht ins flüchtige Arbeitsverzeichnis: ein fehlendes Skript verzögerte Phase 2 um 14 Minuten, und die Meldung „freigegeben“ war falsch. Agenten rekonstruieren Einzelzeiten nachträglich, wenn sie Aufgaben in einem Block bearbeiten.
