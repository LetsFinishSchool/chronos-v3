---
title: E-002 Spike-Ergebnisse (TypeScript, Go, Rust)
type: concept
sources:
  - docs/arc42/09-entscheidungen/ADR-004-sprache-und-laufzeit.md
  - docs/arc42/09-entscheidungen/E-002-spike-kriterien.md
  - spikes/e-002/ (lokal, Berichte und Ergebnisse sind git-ignoriert)
confidence: mittel
last-verified: 2026-11-23
---

# E-002 Spike-Ergebnisse

**Stand 2026-11-23.** Vier Agenten (TypeScript, Go, Rust, Python; Sonnet 5.5, nicht Opus: Nutzungslimit) bauten in einer Vagrant-VM denselben Durchstich (V-1) in TypeScript, Go und Rust. Alle bestehen die Abnahme (K1 bis K7, K3 manuell durch den Product Owner). Phase 1 dauerte 12, 19 und 34 min, nicht 8 h.

**Gesamtpunkte** (ADR-001-Gewichte): TypeScript 87,0, Go 86,1, Rust 90,8. Rust liegt in allen drei Rechnungen vorn, aber mit 3,1 bis 3,8 Punkten Vorsprung (Regel: 5). **Entschieden und freigegeben (PO 2026-11-23): ADR-004, Rust** mit `rrule` (isoliert, Differenztest gegen dateutil, `jiff` als Plan B), `web-push-native` (K3 bestanden) und Pipeline-Prüfung der Sicherheitsmeldungen; Python bestätigt ausgeschieden.

**Lehren für künftige Spikes und Agentenläufe**
- Das Nutzungslimit des Kontos ist ein Fremdlimit der Agenten: Drei parallele Opus-Agenten erreichten es in 7 Minuten. Vor dem Start Limit und Modell klären, sonst Läufe nacheinander oder mit Sonnet.
- Die VM-Festplatte (31 GB) füllte sich durch Rust-`target`-Verzeichnisse (4 bis 5 GB je Klon) und Docker-Images. Vor Messungen `df` prüfen, Docker-Cache und Archive entfernen.
- Eine Aufgabenbeschreibung darf Endpunkte nicht nur in Testseiten voraussetzen (V-1 ohne `GET /api/v1/push/vapid-public-key`): Nur ein Agent baute ihn, der manuelle Test K3 scheiterte bei den anderen scheinbar. Alle Verträge gehören in die Spezifikation.
- Browser sperren Port 10080 (und weitere „unsichere“ Ports): lokale Tunnelports außerhalb dieser Liste wählen.
- Docker-Healthchecks von Images (Mailpit prüft Port 8025) schlagen bei verschobenen Ports fehl; `compose up --wait` bricht dann ab, obwohl der Dienst läuft.
- Abhängigkeitszahlen sind nur vergleichbar, wenn dieselbe Definition gilt (Produktions-Build, ohne Entwicklungsabhängigkeiten, bereinigt): Rust 375 Crates, Go 41 Module (146 Pakete), TypeScript 117 Pakete. Die erste Messung (118/209/528) war nicht vergleichbar.
- Agenten messen sich selbst zu optimistisch („Phase 1 in 12 min“): Abnahme und Messung immer unabhängig und aus den Originalskripten, nicht aus Arbeitskopien.

**Python nachträglich (2026-11-23):** Auf Wunsch des Product Owners gebaut (FastAPI, Pydantic, SQLAlchemy asynchron, psycopg 3). Abnahme komplett grün, aber Speicher 212 MiB im Leerlauf (Wertung 0 Punkte), p95 58 ms, Start 4,3 s, 27 Verbindungen, Eigenbau 9,2 %. Vorläufig 71,2 / 70,5 / 62,4 Punkte (Q neutral), selbst im günstigsten Fall unter 80. Befunde der Code-Prüfung: synchrone RRULE-Ausdehnung blockiert die Ereignisschleife (4,5 s bei nie treffender Regel), Worker gibt beim Start alle Sperren frei (nur ein Worker, 16 Doppelversuche), `ai.ask` hält eine DB-Transaktion offen. Bestes Bibliotheksbild aller vier (dateutil, authlib, pyjwt, offizielles SDK).

**Folgeexperimente (Rust):** E-002a `rrule` durch eigenes `jiff`-Modul ersetzen (298 Zeilen, Eigenbau-Anteil 12,5 %, Katalog 29/29), E-002b `web-push-native` statt `web-push` (fertig: 12 Crates weniger, Meldungen unverändert, Einzelmaintainer, K3 aussteht).

Siehe auch: [arc42-Entwurf, Stand 2026-11-20](arc42-entwurf-stand.md).

**Lehren aus dem Python-Lauf:** Messwerkzeuge laufen nur fair, wenn die Werkzeuge der Sprache lokal installiert sind (uv im Container verfälschte M-7 und M-12 um den Docker-Start). Startskripte für Agenten (Phase 2) gehören ins Repository, nicht ins flüchtige Arbeitsverzeichnis: ein fehlendes Skript verzögerte Phase 2 um 14 Minuten, und die Meldung „freigegeben“ war falsch. Agenten rekonstruieren Einzelzeiten nachträglich, wenn sie Aufgaben in einem Block bearbeiten.
