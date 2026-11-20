# Isolierte VM für die Spike-Agenten

Vagrant (VirtualBox, Ubuntu 24.04) mit allem, was die drei Agenten brauchen: Docker (rootful, in der VM), Docker Compose, Node 22, Go (aktuelle stabile), Rust (rustup), Claude Code, git, tmux, Python 3.

**Isolation (bewusst):**
- **Kein geteilter Ordner** mit dem Host. Die Agenten sehen weder das Repository noch dein Home-Verzeichnis.
- Agenten laufen als Benutzer `agent` **ohne `sudo`**. Docker-Gruppenzugehörigkeit ist root-gleich **innerhalb der VM** (akzeptiert).
- **Netzsperre** (`spike-firewall.service`): kein Zugriff auf den Host (`10.0.2.2`), das Heimnetz (`192.168.0.0/16`) und Link-Local; DNS und Internet bleiben offen. Mit `sudo` oder Docker-Rechten in der VM aushebelbar, aber der Agent hat kein `sudo`.
- Zwischenablage und Drag-and-Drop deaktiviert. VM-Name `chronos-spike-agents`.
- **Residual:** Im NAT-Netz ist ein Ausbruch über Fehler in VirtualBox theoretisch möglich; Internetzugang und KI-Schlüssel (nur K6-Proxy) sind in der VM erreichbar.

## Aufbau
```sh
cd spikes/e-002/vm
# Voraussetzung: Arbeitsbereiche in ~/spikes/e-002 (../prepare_workspace.sh)
./make-payload.sh    # packt die Arbeitsbereiche (nur wenn sie noch keine Agentenarbeit enthalten) und den KI-Schlüssel
vagrant up           # baut und provisioniert (ca. 10 min)
```

## Anmeldung von Claude Code (einmalig, interaktiv)
```sh
vagrant ssh
sudo -u agent -i
claude          # /login ausführen, im Browser anmelden, Code einfügen, danach /exit
exit; exit
```

## Agenten starten
```sh
./wait-and-start.sh claude-opus-5-5        # wartet auf die Anmeldung, startet dann alle drei
# oder von Hand:
vagrant ssh -c 'sudo -u agent ~agent/start-agents.sh claude-opus-5-5'
```
Je Kandidat eine tmux-Sitzung `spike-<name>` (nur über `vagrant ssh`, dort `sudo -u agent tmux ls`). `timeout 8h` erzwingt die Zeitbox. Logs: `/home/agent/spikes/e-002/<name>.log`.

## Beobachten
```sh
vagrant ssh -c 'sudo -u agent bash -lc "for l in typescript go rust; do echo == \$l; git -C ~/spikes/e-002/\$l log --oneline | head -3; tail -3 ~/spikes/e-002/\$l/\$l/PROTOKOLL.md; done"'
vagrant ssh -c 'sudo -u agent tmux attach -t spike-go'     # zuschauen, Abtrennen mit Strg-b d
```

## Phase 2 und Ergebnisse
Phase 2 in der VM freigeben (`~/spikes/e-002/...` ist dort der Arbeitsbereich):
```sh
```
`release_phase2.sh` liegt im Repository, nicht in der VM. Lege `PHASE2.md` aus `briefing/PHASE2.md` ab:
```sh
vagrant ssh -c 'sudo tee /home/agent/spikes/e-002/typescript/PHASE2.md >/dev/null' < ../briefing/PHASE2.md
vagrant ssh -c 'sudo -u agent bash -lc "cd ~/spikes/e-002/typescript && git log --format=%s | grep -qx PHASE-1-FERTIG && claude -c -p \"Phase 2 liegt in PHASE2.md. Setze sie um.\" --model claude-opus-5-5 --dangerously-skip-permissions"'
```
Ergebnisse holen (zur Abnahme auf dem Host): `vagrant ssh -c 'sudo tar -C /home/agent/spikes/e-002 -czf - typescript go rust' > ergebnisse.tgz`, danach auf dem Host entpacken und `check_no_secrets.sh` ausführen, bevor irgendetwas ins Repository kommt.

## Abbau
`vagrant destroy -f` löscht VM und Schlüssel darin.
