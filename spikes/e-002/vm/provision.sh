#!/usr/bin/env bash
# Läuft als root in der VM (einmalig): Werkzeuge, Benutzer 'agent' ohne sudo, Netzsperre, Nutzlast.
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg git build-essential pkg-config libssl-dev jq tmux rsync bc unzip \
  python3 python3-venv docker.io docker-compose-v2 iptables
systemctl enable --now docker

# Node.js 22 und Claude Code
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
npm install -g @anthropic-ai/claude-code

# Go: aktuelle stabile Version von go.dev
gov=$(curl -fsSL 'https://go.dev/dl/?mode=json' | jq -r '[.[] | select(.stable)][0].version')
curl -fsSL "https://go.dev/dl/${gov}.linux-amd64.tar.gz" | tar -C /usr/local -xz
echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin' > /etc/profile.d/spike-tools.sh

# Benutzer ohne sudo; Docker-Gruppe (in der VM, daher akzeptiert)
id agent >/dev/null 2>&1 || useradd -m -s /bin/bash agent
usermod -aG docker agent
sudo -u agent bash -c 'curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal'
sudo -u agent git config --global user.name spike
sudo -u agent git config --global user.email spike@example.test

# Infrastruktur-Images vorab ziehen (für alle Kandidaten gleich; Kandidaten-Basisimages ziehen die Agenten selbst)
for i in postgres:17-alpine quay.io/keycloak/keycloak:26.1.5 axllent/mailpit:latest python:3.13-alpine; do docker pull -q "$i"; done

# Nutzlast
install -d -o agent -g agent -m 755 /home/agent/spikes
tar -C /home/agent/spikes -xzf /tmp/spikes.tgz
mkdir -p /home/agent/spikes/e-002 && for l in typescript go rust; do rm -rf /home/agent/spikes/e-002/$l; mv /home/agent/spikes/$l /home/agent/spikes/e-002/$l; done
install -d -o agent -g agent -m 700 /home/agent/.config/chronos-spike
[ -s /tmp/anthropic.env ] && install -o agent -g agent -m 600 /tmp/anthropic.env /home/agent/.config/chronos-spike/anthropic.env
install -o agent -g agent -m 755 /tmp/start-agents.sh /home/agent/start-agents.sh
chown -R agent:agent /home/agent/spikes
rm -f /tmp/spikes.tgz /tmp/anthropic.env /tmp/start-agents.sh

# Netzsperre (ganz am Ende, damit die Provisionierung nicht gestört wird): kein Zugriff auf den Host (NAT-Gateway 10.0.2.2) und das Heimnetz; DNS (10.0.2.3) und Internet bleiben offen
cat > /usr/local/sbin/spike-firewall.sh <<'EOT'
#!/bin/sh
iptables -N SPIKE_BLOCK 2>/dev/null || iptables -F SPIKE_BLOCK
iptables -A SPIKE_BLOCK -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN   # Antworten (z. B. SSH vom Host) bleiben möglich
iptables -A SPIKE_BLOCK -d 10.0.2.3 -j RETURN
iptables -A SPIKE_BLOCK -d 10.0.2.2 -j REJECT
iptables -A SPIKE_BLOCK -d 192.168.0.0/16 -j REJECT
iptables -A SPIKE_BLOCK -d 169.254.0.0/16 -j REJECT
iptables -C OUTPUT -j SPIKE_BLOCK 2>/dev/null || iptables -I OUTPUT 1 -j SPIKE_BLOCK
EOT
chmod 755 /usr/local/sbin/spike-firewall.sh
cat > /etc/systemd/system/spike-firewall.service <<'EOT'
[Unit]
Description=Spike-VM Netzsperre
After=network-online.target docker.service
Wants=network-online.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/spike-firewall.sh
[Install]
WantedBy=multi-user.target
EOT
systemctl daemon-reload && systemctl enable --now spike-firewall.service

# Kurzbericht
for t in docker node npm claude go git; do printf '%s: ' $t; (command -v $t >/dev/null && ($t --version 2>&1 | head -1)) || echo FEHLT; done
sudo -u agent bash -lc 'source ~/.cargo/env; cargo --version'
docker compose version
