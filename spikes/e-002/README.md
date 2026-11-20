# Spike E-002 (Sprachwahl)

Vergleich von TypeScript, Go und Rust nach `docs/arc42/09-entscheidungen/E-002-spike-kriterien.md`. Die Kandidaten werden von Agenten umgesetzt (je 8 h, parallel, isoliert). Ablauf: [RUNBOOK.md](RUNBOOK.md).

```
common/
  V-1-aufgabenbeschreibung.md   Aufgabe und HTTP-Verträge (für alle gleich)
  acceptance/                   V-2 Abnahmesuite (HTTP-Blackbox), Golden-Daten, manueller Test K3
  bridge-check/                 Prüfdateien für die Frontend-Brücke (S-10)
  env/                          V-4 Umgebung (compose, Realm, Mock-Kanal, KI-Schutz-Proxy, Push-Testseite, stack.sh)
  measure/                      V-3 Mess- und Auswertungsskripte
briefing/                       V-5 Briefing-Vorlage, Phase 2, Kandidatenvorgaben
reference/                      Referenzattrappe (kein Kandidat), validiert Suite und Umgebung
prepare_workspace.sh            V-5 isolierter Arbeitsbereich je Agent
release_phase2.sh               Phase 2 freigeben
check_no_secrets.sh             V-6/RB-008 Geheimnisprüfung
typescript/ go/ rust/           Lieferungen der Kandidaten (entstehen in den Arbeitsbereichen)
```

Stand der Vorbereitung (siehe Kriteriendokument, Abschnitt 2a):

| | Artefakt | Stand |
|---|---|---|
| V-1 | Aufgabenbeschreibung | fertig (Entwurf) |
| V-2 | Abnahmesuite (65 Tests) | gegen die Referenzattrappe validiert (inkl. K6 mit echtem KI-Aufruf), **ohne** K3 (manuell) |
| V-3 | Last-, Mess- und Auswertungsskripte | Rauchtest gegen die Attrappe bestanden (Messung, Auswertung); Volllauf 3 × 15 min steht aus |
| V-4 | Container-Umgebung | läuft (rootless Docker, Host-Netz); Portversätze 0/1000/2000 |
| V-5 | Briefing und Arbeitsbereiche | fertig, `prepare_workspace.sh` geprüft |
| V-6 | Anthropic-Zugang | Schlüssel liegt bereit (`~/.config/chronos-spike/anthropic.env`, Modus 600). **Technisches Kostenlimit eingebaut** (Schutz-Proxy `ai-guard`, getestet); K6 bestanden. Ausgabenlimit in der Konsole als zweite Linie empfohlen, nicht prüfbar |

Dieses Verzeichnis liegt im Arbeitszweig `new-requirements` und gehört nicht in den Hauptzweig.
