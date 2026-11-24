"""Zeichnet den Crate-Zuschnitt (docs/arc42/05-bausteine/02-crate-zuschnitt.md) als Excalidraw und SVG.

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
                "arc42 Kapitel 5, Crate-Zuschnitt (freigegeben 2026-11-24). Pfeil A → B: A darf von B abhängen. Rot gestrichelt: verbotene Kante.")
    d.boundary("WS", 40, 100, 1640, 610, "Cargo-Workspace (crates/)")

    d.box("CH", 655, 150, 400, 110, "chronos", "system", tech="Binary, crates/chronos",
          desc="Unterbefehle serve, worker, migrate; einziger Ort, an dem alles zusammengesteckt wird")

    y, w, h = 340, 230, 140
    d.box("WEB", 80, y, w, h, "chronos-web", "component", tech="crates/web",
          desc="HTTP, Oberfläche ausliefern, Sitzung, Feed, Assistent")
    d.box("DOM", 410, y, w, h, "chronos-domain", "component", tech="crates/domain",
          desc="Fachbereiche: Teams, Termine, ...")
    d.box("CHA", 740, y, w, h, "chronos-channels", "component", tech="crates/channels",
          desc="Zustellkanäle: Web Push, E-Mail")
    d.box("WRK", 1070, y, w, h, "chronos-worker", "component", tech="crates/worker",
          desc="Outbox, Benachrichtigung, Zeitauslöser")
    d.box("ADA", 1400, y, w, h, "chronos-adapters", "component", tech="crates/adapters",
          desc="Keycloak, KI-Gateway, Ferien-Quelle, Backup (ein Modul je Adapter)")

    d.box("COR", 80, 580, 1550, 100, "chronos-core", "container", tech="crates/core",
          desc="Operationsschicht und Rahmen, Kontext, Fehler, Zeit, Kostenerfassung; hängt von nichts im Workspace ab")

    # erlaubte Kanten (Reihenfolge = Excalidraw-Kennung e-0 ...)
    d.edge("CH", "WEB")
    d.edge("CH", "DOM", "use chronos_domain as _", lt=0.45)
    d.edge("CH", "CHA")
    d.edge("CH", "WRK")
    d.edge("CH", "ADA")
    d.edge("CH", "COR", via=[(1660, 205), (1660, 630)])
    d.edge("WEB", "COR", "ruft Operationen")
    d.edge("DOM", "COR", "registriert Operationen")
    d.edge("CHA", "COR", "Ereignistypen")
    d.edge("WRK", "COR", "arbeitet Outbox ab")
    d.edge("ADA", "COR")
    d.edge("WRK", "CHA", "stellt zu")
    d.edge("WRK", "ADA", "Heartbeat")
    d.edge("WEB", "ADA", via=[(195, 530), (1515, 530)])

    # verbotene Kanten
    d.edge("WEB", "DOM", "✗ Regel 1", dashed=True)
    d.edge("DOM", "CHA", "✗ Regel 2", dashed=True)

    d.box("NOTE", 80, 740, 1550, 120, "Regeln und Sicherung", "node",
          desc="Regel 1: Clients (web) greifen nur über die Operationsschicht zu und kennen domain nicht. "
               "Regel 2: Fachbereiche (domain) erzeugen nur Ereignisse und kennen weder channels noch adapters. "
               "Gesichert durch: Positivliste der Kanten als Test über cargo metadata (schützt auch vor Änderungen an der Cargo.toml); "
               "der Compiler verhindert Importe ohne Eintrag; cargo-deny (bans, wrappers) beschränkt Bibliotheken je Crate.")
    d.add_legend([("system", "Binary"), ("component", "Crate"), ("container", "Kern"), ("node", "Hinweis")])
    return d, {"e-14", "e-15"}


def main():
    d, forbidden = build()
    data = d.to_excalidraw()
    for el in data["elements"]:
        if el["id"] in forbidden:
            el["strokeColor"] = RED
    data["source"] = "chronos-v3/wiki/diagramme/crate-zuschnitt.py"
    with open(os.path.join(HERE, "crate-zuschnitt.excalidraw"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    svg = d.to_svg()
    idx = {int(k.split("-")[1]) for k in forbidden}
    cnt = [-1]

    def sub(m):
        cnt[0] += 1
        s = m.group(0)
        return s.replace('stroke="#555"', 'stroke="%s"' % RED) if cnt[0] in idx else s
    svg = re.sub(r'<path d="[^"]*" fill="none" stroke="#555"[^>]*>', sub, svg)
    with open(os.path.join(HERE, "crate-zuschnitt.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    print("ok")


if __name__ == "__main__":
    main()
