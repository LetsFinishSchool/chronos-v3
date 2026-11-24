"""Zeichnet den vorgeschlagenen Crate-Zuschnitt (Task #99, ADR-009, Kapitel 5) als Excalidraw und SVG.

Nutzt die Bibliothek c4lib aus docs/arc42/diagramme/generator (nur lesend).
Aufruf: python3 crate-zuschnitt.py   (schreibt in dieses Verzeichnis)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "docs", "arc42", "diagramme", "generator"))
from c4lib import Diagram  # noqa: E402

RED = "#c92a2a"


def build():
    d = Diagram("crate-zuschnitt", "Cargo-Workspace: Crates und erlaubte Abhängigkeiten",
                "Vorschlag für Task #99 (ADR-009, Kapitel 5). Pfeil A → B: A darf von B abhängen. Rot gestrichelt: verbotene Kante.")
    d.boundary("WS", 40, 100, 1640, 610, "Cargo-Workspace (crates/)")

    # Binary
    d.box("CH", 640, 150, 400, 110, "chronos", "system", tech="Binary, crates/chronos",
          desc="Unterbefehle serve, worker, migrate; einziger Ort, an dem alles zusammengesteckt wird")

    # Reihe: web, domain, channels, worker
    y, w, h = 340, 260, 140
    d.box("WEB", 80, y, w, h, "chronos-web", "component", tech="crates/web",
          desc="HTTP, Auslieferung der Oberfläche, Sitzung")
    d.box("DOM", 500, y, w, h, "chronos-domain", "component", tech="crates/domain",
          desc="Fachbereiche: Teams, Termine, ...")
    d.box("CHA", 920, y, w, h, "chronos-channels", "component", tech="crates/channels",
          desc="Kanäle: Web Push, E-Mail")
    d.box("WRK", 1340, y, w, h, "chronos-worker", "component", tech="crates/worker",
          desc="Outbox abarbeiten, Zeitauslöser, Benachrichtigung")

    # Kern
    d.box("COR", 80, 580, 1520, 100, "chronos-core", "container", tech="crates/core",
          desc="Operationsschicht und Rahmen, Kontext, Fehler, Zeit; hängt von nichts im Workspace ab")

    # erlaubte Kanten
    d.edge("CH", "WEB")
    d.edge("CH", "DOM", "use chronos_domain as _ (inventory)", lt=0.45)
    d.edge("CH", "CHA")
    d.edge("CH", "WRK")
    d.edge("CH", "COR", via=[(1640, 205), (1640, 630)])
    d.edge("WEB", "COR", "ruft Operationen")
    d.edge("DOM", "COR", "registriert Operationen")
    d.edge("CHA", "COR", "Ereignistypen")
    d.edge("WRK", "COR", "arbeitet Outbox ab")
    d.edge("WRK", "CHA", "stellt zu")

    # verbotene Kanten (Kapitel 5, Regel 1 und 2)
    d.edge("WEB", "DOM", "✗ Regel 1", dashed=True, lt=0.5)
    d.edge("DOM", "CHA", "✗ Regel 2", dashed=True, lt=0.5)

    d.box("NOTE", 80, 740, 1520, 120, "Regeln und Sicherung", "node",
          desc="Regel 1 (Kapitel 5): Clients (web) greifen nur über die Operationsschicht zu, deshalb kennt web die Fachbereiche nicht. "
               "Regel 2: Fachbereiche erzeugen nur Ereignisse und kennen keine Kanäle. "
               "Gesichert durch: Positivliste der Kanten als Test über cargo metadata (schützt auch vor Änderungen an der Cargo.toml); "
               "der Compiler verhindert Importe ohne Eintrag; cargo-deny (bans, wrappers) beschränkt Bibliotheken je Crate.")
    d.add_legend([("system", "Binary"), ("component", "Crate (Baustein)"), ("container", "Kern"), ("node", "Hinweis")])
    return d, {"e-10", "e-11"}


def main():
    d, forbidden = build()
    # Excalidraw: verbotene Kanten rot
    data = d.to_excalidraw()
    for el in data["elements"]:
        if el["id"] in forbidden:
            el["strokeColor"] = RED
    data["source"] = "chronos-v3/wiki/diagramme/crate-zuschnitt.py"
    with open(os.path.join(HERE, "crate-zuschnitt.excalidraw"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    # SVG: Kantenpfade (fill="none") in Reihenfolge der Kanten
    svg = d.to_svg()
    idx = {int(k.split("-")[1]) for k in forbidden}
    cnt = [-1]

    def sub(m):
        cnt[0] += 1
        s = m.group(0)
        return s.replace('stroke="#555"', 'stroke="%s"' % RED) if cnt[0] in idx else s
    svg = re.sub(r'<path d="[^"]*" fill="none" stroke="#555"[^>]*>', lambda m: sub(m), svg)
    svg = svg.replace('<path d="M0,0 L10,4 L0,8 z" fill="#555"/>', '<path d="M0,0 L10,4 L0,8 z" fill="#555"/>')
    with open(os.path.join(HERE, "crate-zuschnitt.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    print("ok")


if __name__ == "__main__":
    main()
