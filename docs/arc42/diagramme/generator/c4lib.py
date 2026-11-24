"""Kleine C4-Bibliothek: erzeugt .excalidraw-Dateien und eine SVG-Vorschau aus demselben Modell.

Aufruf: python3 generate.py   (schreibt alle Diagramme in dieses Verzeichnis)
"""
import json
import math
import random

# C4-Standardfarben (Fuellung, Rand, Schrift)
KINDS = {
    "person":    ("#08427b", "#052e56", "#ffffff"),
    "system":    ("#1168bd", "#0b4884", "#ffffff"),
    "external":  ("#8a8a8a", "#6b6b6b", "#ffffff"),
    "container": ("#438dd5", "#2e6295", "#ffffff"),
    "database":  ("#438dd5", "#2e6295", "#ffffff"),
    "component": ("#85bbf0", "#5d82a8", "#0b1f33"),
    "node":      ("#f4f4f4", "#888888", "#222222"),
}
FONT = 14
LINE = 19  # Zeilenhoehe


def wrap(text, width_px, size=FONT):
    maxc = max(8, int((width_px - 24) / (size * 0.56)))
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            if line and len(line) + 1 + len(w) > maxc:
                out.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        out.append(line)
    return out


class Diagram:
    def __init__(self, name, title, subtitle=""):
        self.name, self.title, self.subtitle = name, title, subtitle
        self.nodes = {}   # id -> dict
        self.edges = []
        self.bounds = []
        self.legend = []
        self.seed = 1000

    # --- Modell -----------------------------------------------------
    def box(self, id, x, y, w, h, name, kind="container", tech=None, desc=None, dashed=False):
        lines = [("b", name)]
        if tech:
            lines.append(("i", "[" + tech + "]"))
        self.nodes[id] = dict(id=id, x=x, y=y, w=w, h=h, kind=kind, dashed=dashed,
                              name=name, tech=tech, desc=desc, label=None)
        text = name + ("\n[" + tech + "]" if tech else "") + ("\n" + desc if desc else "")
        self.nodes[id]["text"] = text
        return id

    def boundary(self, id, x, y, w, h, label, dashed=True):
        self.bounds.append(dict(id=id, x=x, y=y, w=w, h=h, label=label, dashed=dashed))
        self.nodes[id] = dict(id=id, x=x, y=y, w=w, h=h, kind="node", dashed=dashed, name=label,
                              tech=None, desc=None, label=None, text="", hidden=True)

    def edge(self, a, b, label="", dashed=False, both=False, via=None, off=0, lt=0.5):
        self.edges.append(dict(a=a, b=b, label=label, dashed=dashed, both=both, via=via, off=off, lt=lt))

    def add_legend(self, kinds):
        self.legend = kinds

    # --- Geometrie --------------------------------------------------
    def _clip(self, n, tx, ty):
        """Schnittpunkt der Strecke Mitte(n)->(tx,ty) mit dem Rechteck von n."""
        cx, cy = n["x"] + n["w"] / 2, n["y"] + n["h"] / 2
        dx, dy = tx - cx, ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        sx = (n["w"] / 2) / abs(dx) if dx else math.inf
        sy = (n["h"] / 2) / abs(dy) if dy else math.inf
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s

    def _edge_points(self, e):
        a, b = self.nodes[e["a"]], self.nodes[e["b"]]
        bc = (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
        ac = (a["x"] + a["w"] / 2, a["y"] + a["h"] / 2)
        if e["via"]:
            pts = [self._clip(a, *e["via"][0])] + [tuple(p) for p in e["via"]] + [self._clip(b, *e["via"][-1])]
        else:
            off = e.get("off", 0)
            if off:
                dx, dy = bc[0] - ac[0], bc[1] - ac[1]
                ln = math.hypot(dx, dy) or 1
                px, py = -dy / ln * off, dx / ln * off
                ac, bc = (ac[0] + px, ac[1] + py), (bc[0] + px, bc[1] + py)
                pa = self._clip_pt(a, ac, bc)
                pb = self._clip_pt(b, bc, ac)
                return [pa, pb]
            pts = [self._clip(a, *bc), self._clip(b, *ac)]
        return pts

    def _clip_pt(self, n, c, t):
        """Austrittspunkt des Strahls von c (innerhalb n) in Richtung t aus dem Rechteck n."""
        cx, cy = n["x"] + n["w"] / 2, n["y"] + n["h"] / 2
        dx, dy = t[0] - c[0], t[1] - c[1]
        px, py = c[0] - cx, c[1] - cy
        ts = []
        if dx:
            ts.append(((n["w"] / 2 if dx > 0 else -n["w"] / 2) - px) / dx)
        if dy:
            ts.append(((n["h"] / 2 if dy > 0 else -n["h"] / 2) - py) / dy)
        k = min(ts)
        return c[0] + dx * k, c[1] + dy * k

    # --- Excalidraw -------------------------------------------------
    def _rid(self):
        self.seed += 1
        return self.seed

    def _base(self, id, typ, x, y, w, h, **kw):
        d = dict(id=id, type=typ, x=x, y=y, width=w, height=h, angle=0,
                 strokeColor="#1e1e1e", backgroundColor="transparent", fillStyle="solid",
                 strokeWidth=1, strokeStyle="solid", roughness=0, opacity=100, groupIds=[],
                 frameId=None, roundness=None, seed=self._rid(), version=1, versionNonce=self._rid(),
                 isDeleted=False, boundElements=[], updated=1, link=None, locked=False)
        d.update(kw)
        return d

    def _text(self, id, x, y, lines, color, size=FONT, container=None, align="center", valign="middle", w=None, h=None):
        text = "\n".join(lines)
        tw = w if w is not None else max(len(l) for l in lines) * size * 0.56
        th = h if h is not None else len(lines) * LINE
        return self._base(id, "text", x, y, tw, th, strokeColor=color, text=text, originalText=text,
                          fontSize=size, fontFamily=2, textAlign=align, verticalAlign=valign,
                          containerId=container, lineHeight=1.35, autoResize=True, baseline=size)

    def to_excalidraw(self):
        els = []
        # Titel
        els.append(self._text("title", 40, 20, [self.title], "#1e1e1e", 24, align="left", valign="top", w=900, h=30))
        if self.subtitle:
            els.append(self._text("subtitle", 40, 54, [self.subtitle], "#555555", 14, align="left", valign="top", w=1200, h=20))
        for b in self.bounds:
            els.append(self._base("bd-" + b["id"], "rectangle", b["x"], b["y"], b["w"], b["h"],
                                  strokeColor="#555555", strokeStyle="dashed" if b["dashed"] else "solid",
                                  roundness={"type": 3}))
            els.append(self._text("bdt-" + b["id"], b["x"] + 12, b["y"] + 8, [b["label"]], "#444444", 14,
                                  align="left", valign="top", w=b["w"] - 24, h=20))
        bound_ids = {}
        for b in self.bounds:
            bound_ids[b["id"]] = "bd-" + b["id"]
        for n in self.nodes.values():
            if n.get("hidden"):
                continue
            fill, stroke, fg = KINDS[n["kind"]]
            rid = "n-" + n["id"]
            rect = self._base(rid, "rectangle", n["x"], n["y"], n["w"], n["h"], strokeColor=stroke,
                              backgroundColor=fill, strokeStyle="dashed" if n["dashed"] else "solid",
                              roundness={"type": 3}, strokeWidth=2 if n["kind"] == "database" else 1)
            lines = wrap(n["text"], n["w"])
            th = len(lines) * LINE
            tid = "t-" + n["id"]
            txt = self._text(tid, n["x"] + 12, n["y"] + (n["h"] - th) / 2, lines, fg, container=rid,
                             w=n["w"] - 24, h=th)
            rect["boundElements"].append({"id": tid, "type": "text"})
            bound_ids[n["id"]] = rid
            els += [rect, txt]
        for i, e in enumerate(self.edges):
            pts = self._edge_points(e)
            x0, y0 = pts[0]
            rel = [[p[0] - x0, p[1] - y0] for p in pts]
            xs, ys = [p[0] for p in rel], [p[1] for p in rel]
            aid = "e-%d" % i
            arrow = self._base(aid, "arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys),
                               strokeColor="#555555", strokeStyle="dashed" if e["dashed"] else "solid",
                               points=rel, lastCommittedPoint=None, startArrowhead="arrow" if e["both"] else None,
                               endArrowhead="arrow", roundness={"type": 2},
                               startBinding={"elementId": bound_ids[e["a"]], "focus": 0, "gap": 2},
                               endBinding={"elementId": bound_ids[e["b"]], "focus": 0, "gap": 2})
            for nid in (e["a"], e["b"]):
                for el in els:
                    if el["id"] == bound_ids[nid]:
                        el["boundElements"].append({"id": aid, "type": "arrow"})
            els.append(arrow)
            if e["label"]:
                lines = wrap(e["label"], 200)
                lid = "el-%d" % i
                mx, my = self._midpoint(pts, e["lt"])
                lw = max(len(l) for l in lines) * FONT * 0.56
                lh = len(lines) * LINE
                els.append(self._text(lid, mx - lw / 2, my - lh / 2, lines, "#333333", FONT - 1,
                                      container=aid, w=lw, h=lh))
                arrow["boundElements"].append({"id": lid, "type": "text"})
        # Legende
        lx, ly = 40, self._max_y() + 30
        els.append(self._text("lg-title", lx, ly, ["Legende"], "#444444", 14, align="left", valign="top", w=100, h=20))
        for j, (kind, label) in enumerate(self.legend):
            fill, stroke, fg = KINDS[kind]
            els.append(self._base("lg-r%d" % j, "rectangle", lx + j * 230, ly + 26, 28, 18, strokeColor=stroke,
                                  backgroundColor=fill, roundness={"type": 3}))
            els.append(self._text("lg-t%d" % j, lx + j * 230 + 36, ly + 26, [label], "#333333", 13, align="left",
                                  valign="middle", w=180, h=18))
        return {"type": "excalidraw", "version": 2, "source": "chronos-v3/docs/arc42/diagramme/generator",
                "elements": els, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
                "files": {}}

    def _midpoint(self, pts, t=0.5):
        # Punkt bei Anteil t der Gesamtlaenge, auf dem laengsten Segment gemittelt bei Umwegen
        if len(pts) == 2:
            return pts[0][0] + (pts[1][0] - pts[0][0]) * t, pts[0][1] + (pts[1][1] - pts[0][1]) * t
        segs = list(zip(pts, pts[1:]))
        a, b = max(segs, key=lambda sg: math.hypot(sg[1][0] - sg[0][0], sg[1][1] - sg[0][1]))
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2

    def _max_y(self):
        ys = [n["y"] + n["h"] for n in self.nodes.values()] + [b["y"] + b["h"] for b in self.bounds]
        return max(ys)

    # --- SVG-Vorschau -----------------------------------------------
    def to_svg(self):
        W = max([n["x"] + n["w"] for n in self.nodes.values()] + [b["x"] + b["w"] for b in self.bounds]) + 60
        H = self._max_y() + 120
        o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
             '<defs><marker id="a" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto-start-reverse"><path d="M0,0 L10,4 L0,8 z" fill="#555"/></marker></defs>',
             '<rect width="100%" height="100%" fill="#fff"/>',
             '<text x="40" y="44" font-size="24" font-weight="bold">%s</text>' % esc(self.title)]
        if self.subtitle:
            o.append('<text x="40" y="68" font-size="14" fill="#555">%s</text>' % esc(self.subtitle))
        for b in self.bounds:
            o.append('<rect x="%s" y="%s" width="%s" height="%s" rx="10" fill="none" stroke="#555" %s/>' % (
                b["x"], b["y"], b["w"], b["h"], 'stroke-dasharray="8 6"' if b["dashed"] else ""))
            o.append('<text x="%s" y="%s" font-size="14" fill="#444">%s</text>' % (b["x"] + 12, b["y"] + 24, esc(b["label"])))
        for n in self.nodes.values():
            if n.get("hidden"):
                continue
            fill, stroke, fg = KINDS[n["kind"]]
            o.append('<rect x="%s" y="%s" width="%s" height="%s" rx="8" fill="%s" stroke="%s" %s/>' % (
                n["x"], n["y"], n["w"], n["h"], fill, stroke, 'stroke-dasharray="6 4"' if n["dashed"] else ""))
            lines = wrap(n["text"], n["w"])
            y0 = n["y"] + (n["h"] - len(lines) * LINE) / 2 + 14
            for k, l in enumerate(lines):
                o.append('<text x="%s" y="%s" font-size="%d" text-anchor="middle" fill="%s">%s</text>' % (
                    n["x"] + n["w"] / 2, y0 + k * LINE, FONT, fg, esc(l)))
        for e in self.edges:
            pts = self._edge_points(e)
            d = "M" + " L".join("%s,%s" % p for p in pts)
            o.append('<path d="%s" fill="none" stroke="#555" stroke-width="1.5" %s marker-end="url(#a)" %s/>' % (
                d, 'stroke-dasharray="6 4"' if e["dashed"] else "", 'marker-start="url(#a)"' if e["both"] else ""))
            if e["label"]:
                lines = wrap(e["label"], 200)
                mx, my = self._midpoint(pts, e["lt"])
                lw = max(len(l) for l in lines) * (FONT - 1) * 0.56 + 8
                lh = len(lines) * LINE
                o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#fff" opacity="0.9"/>' % (mx - lw / 2, my - lh / 2, lw, lh))
                for k, l in enumerate(lines):
                    o.append('<text x="%s" y="%s" font-size="%d" text-anchor="middle" fill="#333">%s</text>' % (
                        mx, my - lh / 2 + 14 + k * LINE, FONT - 1, esc(l)))
        lx, ly = 40, self._max_y() + 30
        o.append('<text x="%s" y="%s" font-size="14" fill="#444">Legende</text>' % (lx, ly + 14))
        for j, (kind, label) in enumerate(self.legend):
            fill, stroke, _ = KINDS[kind]
            o.append('<rect x="%s" y="%s" width="28" height="18" rx="4" fill="%s" stroke="%s"/>' % (lx + j * 230, ly + 26, fill, stroke))
            o.append('<text x="%s" y="%s" font-size="13" fill="#333">%s</text>' % (lx + j * 230 + 36, ly + 40, esc(label)))
        o.append("</svg>")
        return "\n".join(o)

    def write(self, outdir):
        with open("%s/%s.excalidraw" % (outdir, self.name), "w", encoding="utf-8") as f:
            json.dump(self.to_excalidraw(), f, ensure_ascii=False, indent=1)
        with open("%s/%s.svg" % (outdir, self.name), "w", encoding="utf-8") as f:
            f.write(self.to_svg())


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
