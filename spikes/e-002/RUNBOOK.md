# Runbook Spike E-002

Ablauf von der Vorbereitung bis zum Ergebnis (ADR-004). Kriterien: `docs/arc42/09-entscheidungen/E-002-spike-kriterien.md`.

## 0. Einmalig (V-6): KI-Zugang
**Technische Grenze (eingebaut):** Die Spike-Anwendungen sprechen nie direkt mit Anthropic, sondern mit dem Schutz-Proxy `common/env/ai-guard`. Er hält den echten Schlüssel (nur seine `guard.env`) und erzwingt je Umgebung: höchstens 150 Anfragen, 600 000 Eingabe- und 60 000 Ausgabetokens, nur das Modell `claude-haiku-5-5`, `max_tokens` ≤ 1024, kein Streaming, nur `/v1/messages`; danach Antwort 429. Stand: `curl $AI_GUARD_URL/guard/stats`. Rechnerisch bleibt der Verbrauch je Umgebung im niedrigen Cent- bis einstelligen Eurobereich.

**Zusätzlich empfohlen (zweite Linie, nicht prüfbar):**
1. In der Anthropic-Konsole einen **eigenen Arbeitsbereich** mit **Ausgabenlimit** anlegen (z. B. 5 €) und dort einen Schlüssel erzeugen.
2. `mkdir -p ~/.config/chronos-spike && cp common/env/anthropic.env.example ~/.config/chronos-spike/anthropic.env && chmod 600 …` und den Schlüssel eintragen. `stack.sh` liest ihn von dort; er gelangt nur nach `.stack/<name>/app.env` (nicht versioniert, Modus 600).
3. Vor dem Commit und nach jedem Agentenlauf: `./check_no_secrets.sh <verzeichnis>`.

## 1. Vorbereitung prüfen (erledigt, jederzeit wiederholbar)
```sh
cd reference && make build && cd ../common/env && ./stack.sh up reference 0 chronos-spike-reference
eval "$(./stack.sh env reference 0)"
SKIP_AI=1 python3 ../acceptance/run_acceptance.py          # Phase 1: alle grün
python3 ../acceptance/run_acceptance.py --phase 2          # Phase 2: grün
CANDIDATE_DIR=$PWD/../../reference python3 ../acceptance/run_acceptance.py --only S10
./stack.sh down reference 0
```
Die Attrappe ist **kein** Kandidat und dient nur der Validierung. K6 (echter KI-Aufruf) und K3 (Web Push) sind damit **nicht** geprüft.

## 2. Arbeitsbereiche anlegen (V-5)
```sh
./prepare_workspace.sh typescript     # → ~/spikes/e-002/typescript (Portversatz 0)
./prepare_workspace.sh go             # → ~/spikes/e-002/go         (Portversatz 1000)
./prepare_workspace.sh rust           # → ~/spikes/e-002/rust       (Portversatz 2000)
```
Je Kandidat **ein Agent** (gleiches Modell, gleiche Einstellungen), Arbeitsverzeichnis = Arbeitsbereich, erster Auftrag = Inhalt von `START-PROMPT.txt`. Alle drei **parallel**. Jeder Agent sieht nur seinen Arbeitsbereich (ohne die Messskripte und ohne die anderen Kandidaten). Startzeit und Zeitbox (8 h) im Protokoll festhalten.

## 3. Phase 2
Sobald der Agent `PHASE-1-FERTIG` committet hat: `./release_phase2.sh ~/spikes/e-002/<name>`, den Agenten mit „Phase 2 liegt in PHASE2.md. Setze sie um.“ fortsetzen.

## 4. Abnahme und Messung (nacheinander, nicht gleichzeitig)
Für jeden Kandidaten:
```sh
cd ~/spikes/e-002/<name>/<name> && make build
cd ../common/env && ./stack.sh up <name> <offset> chronos-spike-<name> && eval "$(./stack.sh env <name> <offset>)"
export CANDIDATE_DIR=$PWD/../../<name>
python3 ../acceptance/run_acceptance.py --json ../../report-<name>.json       # Phase 1 (K2, K4..K6, M-14, M-15, S-10)
python3 ../acceptance/run_acceptance.py --phase 2                              # Phase 2
# Messungen aus dem Repository (nicht aus dem Arbeitsbereich):
python3 <repo>/spikes/e-002/common/measure/measure.py --image chronos-spike-<name> --out <repo>/spikes/e-002/reports/<name>
<repo>/spikes/e-002/common/measure/eigenbau.py ~/spikes/e-002/<name>/<name>      # M-9
<repo>/spikes/e-002/common/measure/n1_diff.sh ~/spikes/e-002/<name>              # M-11
```
Danach manuell: K3 (`common/acceptance/manual/K3-webpush.md`), M-7, M-8, M-10, M-12 (`common/measure/README.md`), Q-1 bis Q-5 durch den Product Owner. Werte in `candidate-template.json` je Kandidat eintragen, dann:
```sh
python3 common/measure/evaluate.py a.json b.json c.json --md reports/auswertung.md
```
Ergebnis und Begründung als `ADR-004` unter `docs/arc42/09-entscheidungen/` (Entwurf), Protokolle ins Wiki.
