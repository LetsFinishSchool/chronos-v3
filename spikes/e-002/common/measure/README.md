# V-3: Mess- und Auswertungsskripte

| Metrik | Werkzeug | Art |
|---|---|---|
| K1, M-1..M-6, M-13 | `measure.py` | automatisch (3 Läufe, Median) |
| M-7 | `feedback.sh <dir> <quelldatei>` | halbautomatisch |
| M-8 | Werkzeug der Sprache (siehe unten) | manuell |
| M-9 | `eigenbau.py <dir>` (Markierungen `EIGENBAU:BEGIN/END`, vom Briefing verlangt) | automatisch |
| M-10 | `PROTOKOLL.md` und `git log` (Zeit bis Phase 1 fertig, Zahl der Korrekturschleifen) | manuell |
| M-11 | `n1_diff.sh <dir>` | automatisch |
| M-12 | Verfahren unten | manuell |
| M-14, M-15 (Teil), K2, K4..K6 | Abnahmesuite `../acceptance/run_acceptance.py` | automatisch |
| Q-1..Q-5, K3 | Product Owner / `acceptance/manual/K3-webpush.md` | manuell |
| Auswertung | `evaluate.py` (Eingabe: ausgefülltes `candidate-template.json` je Kandidat) | automatisch |

## Messung (K1, M-1..M-6, M-13)
```sh
eval "$(../env/stack.sh env <name> <offset>)"
python3 measure.py --image chronos-spike-<name> --out ../../reports/<name>   # Standard: 3 Läufe à 10 min Last + 5 min Leerlauf
python3 measure.py --image chronos-spike-<name> --runs 1 --duration 20 --idle 5 --burst 80   # Rauchtest
```
Last: 50 dauerhafte Verbindungen, 20 Anfragen/s (90 % lesend, 10 % schreibend, Zähler `appointment.list`, `team.effective_members`, `team.effective_teams`, `appointment.get`), dazu ein Stoß von 1000 schreibenden Anfragen (2000 Zustellungen über den Mock-Kanal mit 50 ms). Gemessen wird der Speicher als `working set` laut `docker stats` (Web + Worker), CPU als Mittel in mCPU (100 % = 1000 mCPU), Latenz clientseitig (p50/p95/p99), PostgreSQL-Verbindungen über `pg_stat_activity`, Startzeit (Web beenden, starten, bis `/healthz` 200) und Image-Größe. PostgreSQL und der Messrechner sind für alle gleich.

**Hinweise:** Die Messung läuft auf dem Entwicklungsrechner (amd64, rootless Docker), nicht auf dem Cluster. Werte sind **relativ vergleichbar**, nicht als Cluster-Prognose zu lesen. Parallele Messungen mehrerer Kandidaten verfälschen sich gegenseitig: **Messungen nacheinander ausführen**, nicht gleichzeitig.

## M-8 (Abhängigkeiten und Schwachstellen)
- TypeScript: `npm ls --all --parseable | wc -l`, `npm audit --omit=dev`
- Go: `go list -m all | wc -l`, `govulncheck ./...`
- Rust: `cargo tree --prefix none | sort -u | wc -l`, `cargo audit` (oder `cargo deny check advisories`)

## M-12 (Architekturverstoß)
1. Ausgangslage: `make arch-check` endet mit 0.
2. Im Fachmodul (Termine) eine Abhängigkeit auf das Kanalmodul (`mock`) einbauen (Import bzw. `use`/`import`, Aufruf einer Funktion).
3. `make arch-check` ausführen und die Zeit messen; erwartet: Exit ≠ 0 mit einer Meldung, die Datei oder Regel nennt.
4. Verstoß zurücknehmen. Ergebnis eintragen: `M12_detected` (true/false) und `M12_seconds`.

## Bekannte Auslegungen bei der Auswertung
- M-12: Erkannt und ≤ 10 s = 10 Punkte, danach linear bis 5 Punkte bei 120 s; nicht erkannt = 0 (im Kriteriendokument stehen nur die Endpunkte).
- Zusammengesetzte Metriken (M-8, M-10, M-11, M-15) mitteln ihre zwei Teilwerte; Teilwerte siehe `evaluate.py`.
