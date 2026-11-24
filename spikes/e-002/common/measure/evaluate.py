#!/usr/bin/env python3
"""V-3: Auswertung nach Abschnitt 6 des Kriteriendokuments (K.-o., Punkte, Sensitivität, Entscheidungsregel).

    python3 evaluate.py kandidat-typescript.json kandidat-go.json kandidat-rust.json [--md bericht.md]

Eingabe je Kandidat: siehe candidate-template.json (K1..K7 als true/false, M1..M15 als Rohwerte, Q1..Q5 als 1..5).
Die Normierung folgt der Tabelle in E-002-spike-kriterien.md (Ziel = 10 Punkte, Grenze = 0 Punkte, linear).
"""
import argparse
import json
import sys

# (Ziel, Grenze) – bei Ziel < Grenze ist weniger besser
LIN = {"M1": (40, 200), "M2": (100, 400), "M3": (100, 500), "M4": (50, 300), "M5": (1, 10), "M6": (50, 400), "M7": (5, 60),
       "M9": (2, 15), "M13": (6, 30), "M14": (100, 60)}

GOALS = {  # Ziel -> Metriken (aus Abschnitt 5 des Kriteriendokuments)
    "Änderbarkeit": ["M7", "M8", "M9", "M10", "M11", "M12", "Q1", "Q2", "Q4"],
    "Bedienbarkeit": ["M4", "M5", "Q5"],
    "Ressourcen": ["M1", "M2", "M3", "M6", "M13"],
    "Benachrichtigung": ["M14"],
    "Nachvollziehbarkeit": ["M15", "Q3"],
}
ROC = [46, 26, 16, 9, 4]
VARIANTS = {  # Rangfolge der Ziele je Variante
    "Rangfolge ADR-001 (ROC 46/26/16/9/4)": dict(zip(["Änderbarkeit", "Bedienbarkeit", "Ressourcen", "Benachrichtigung", "Nachvollziehbarkeit"], ROC)),
    "Gleiche Gewichte (je 20 %)": {g: 20 for g in GOALS},
    "Ressourcen an Rang 1": dict(zip(["Ressourcen", "Änderbarkeit", "Bedienbarkeit", "Benachrichtigung", "Nachvollziehbarkeit"], ROC)),
}


def lin(v, ziel, grenze):
    if v is None:
        return 0.0
    x = (v - grenze) / (ziel - grenze)
    return 10 * max(0.0, min(1.0, x))


def points(m, c):
    """Punkte (0..10) je Metrik; zusammengesetzte Metriken nach der Tabelle im Kriteriendokument."""
    g = lambda k: c.get(k)
    p = {}
    for k, (z, gr) in LIN.items():
        p[k] = lin(g(k), z, gr)
    p["M8"] = (lin(g("M8_deps"), 50, 500) + lin(g("M8_high_vulns"), 0, 3)) / 2
    p["M10"] = (lin(g("M10_hours"), 2, 8) + lin(g("M10_loops"), 10, 40)) / 2
    p["M11"] = (lin(g("M11_files"), 1, 6) + (10 if g("M11_auto_tool") else 0)) / 2
    if g("M12_detected"):  # Auslegung: erkannt und ≤ 10 s = 10 Punkte, danach linear bis 5 Punkte bei 120 s
        t = g("M12_seconds") or 0
        p["M12"] = 10 if t <= 10 else 10 - 5 * min(1.0, (t - 10) / 110)
    else:
        p["M12"] = 0.0
    p["M15"] = (lin(g("M15_manual_places"), 1, 10) + lin(g("M15_sample_ok"), 10, 5)) / 2
    for i in range(1, 6):
        q = g(f"Q{i}")
        p[f"Q{i}"] = 0.0 if q is None else (q - 1) / 4 * 10
    return p


def score(p, weights):
    total = 0.0
    for goal, ms in GOALS.items():
        total += weights[goal] / 100 * (sum(p[m] for m in ms) / len(ms)) * 10  # 0..100
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--md", default="")
    args = ap.parse_args()
    cands = [json.load(open(f, encoding="utf-8")) for f in args.files]
    lines = ["# Auswertung E-002", ""]
    alive = []
    lines += ["## K.-o.-Kriterien", "", "| Kandidat | " + " | ".join(f"K{i}" for i in range(1, 8)) + " | Ergebnis |", "|---|" + "---|" * 8]
    for c in cands:
        ks = [c["K"].get(f"K{i}") for i in range(1, 8)]
        ok = all(k is True for k in ks)
        lines.append(f"| {c['name']} | " + " | ".join("ja" if k is True else ("nein" if k is False else "offen") for k in ks) + f" | {'im Rennen' if ok else 'ausgeschieden/offen'} |")
        if ok:
            alive.append(c)
    lines.append("")
    if not alive:
        lines.append("Kein Kandidat erfüllt alle K.-o.-Kriterien.")
        out = "\n".join(lines)
        print(out)
        return
    pts = {c["name"]: points(c["M"], c["M"]) for c in alive}
    lines += ["## Punkte je Metrik (0 bis 10)", "", "| Metrik | " + " | ".join(c["name"] for c in alive) + " |", "|---|" + "---|" * len(alive)]
    for m in sorted({k for p in pts.values() for k in p}, key=lambda x: (x[0], int(x[1:]))):
        lines.append(f"| {m} | " + " | ".join(f"{pts[c['name']][m]:.1f}" for c in alive) + " |")
    lines += ["", "## Gesamtpunkte (0 bis 100) und Sensitivität", "", "| Variante | " + " | ".join(c["name"] for c in alive) + " | Sieger | Vorsprung |", "|---|" + "---|" * (len(alive) + 2)]
    winners, leads = [], []
    for vname, w in VARIANTS.items():
        sc = {c["name"]: score(pts[c["name"]], w) for c in alive}
        order = sorted(sc, key=sc.get, reverse=True)
        lead = sc[order[0]] - sc[order[1]] if len(order) > 1 else sc[order[0]]
        winners.append(order[0])
        leads.append(lead)
        lines.append(f"| {vname} | " + " | ".join(f"{sc[c['name']]:.1f}" for c in alive) + f" | {order[0]} | {lead:.1f} |")
    lines.append("")
    if len(set(winners)) == 1 and min(leads) >= 5:
        lines.append(f"**Entscheidungsregel erfüllt:** {winners[0]} gewinnt in allen drei Rechnungen mit mindestens 5 Punkten Vorsprung (kleinster: {min(leads):.1f}). Vorschlag für ADR-004.")
    else:
        lines.append("**Entscheidungsregel nicht erfüllt:** Das Ergebnis ist ein Befund; der Product Owner entscheidet (Gründe im ADR).")
    out = "\n".join(lines)
    print(out)
    if args.md:
        open(args.md, "w", encoding="utf-8").write(out + "\n")


if __name__ == "__main__":
    main()
