"""Erzeugt Wireframes als Excalidraw-Datei und SVG-Vorschau aus einem Modell (nur Standardbibliothek).

Farben, Abstände und Schriftstile kommen aus designs/tokens/tokens.json (heller Modus).
Beschriftungen nennen Tokens in geschweiften Klammern, z. B. {text.primary}; check.py prüft diese Namen.
"""
import json
import os
import re

GENERATOR_DIR = os.path.dirname(os.path.abspath(__file__))
WIREFRAME_DIR = os.path.dirname(GENERATOR_DIR)
TOKENS_PATH = os.path.join(os.path.dirname(WIREFRAME_DIR), "tokens", "tokens.json")

CHAR_WIDTH = {"sans": 0.55, "sans-bold": 0.53, "mono": 0.6}
EXCALIDRAW_FONT = {"sans": 2, "mono": 3}
SVG_FONT = {"sans": "Inter, Helvetica, Arial, sans-serif", "mono": "Cascadia Code, Menlo, monospace"}

CANVAS = "#ffffff"
CHROME_STROKE = "#9ca3af"
CHROME_TEXT = "#4b5563"
ANNOTATION_TEXT = "#374151"

TOKEN_REF = re.compile(r"\{([a-z0-9][a-z0-9.-]*)\}")


class Tokens:
    def __init__(self, path=TOKENS_PATH, mode="light"):
        with open(path, encoding="utf-8") as f:
            self.tree = json.load(f)
        self.mode = mode
        self.names = set()
        self._collect(self.tree, [])

    def _collect(self, node, path):
        if not isinstance(node, dict):
            return
        if "$value" in node:
            self.names.add(public_name(path))
            return
        for key, child in node.items():
            if not key.startswith("$"):
                self._collect(child, path + [key])

    def _node(self, dotted):
        node = self.tree
        for part in dotted.split("."):
            node = node[part]
        return node

    def _resolve(self, value):
        while isinstance(value, str) and value.startswith("{"):
            value = self._node(value[1:-1])["$value"]
        return value

    def color(self, name):
        return self._resolve(self._node("semantic.%s.%s" % (self.mode, name))["$value"])

    def px(self, name):
        return int(self._resolve(self._node(name)["$value"]).removesuffix("px"))

    def type_style(self, name):
        value = self._node("typography.style." + name)["$value"]
        return dict(size=int(value["fontSize"].removesuffix("px")),
                    line=int(value["lineHeight"].removesuffix("px")),
                    bold=value["fontWeight"] >= 600)


def public_name(path):
    """Semantische Tokens heißen ohne Modus (bg.page), weil der Name in Hell und Dunkel gleich ist."""
    if len(path) > 2 and path[0] == "semantic":
        path = path[2:]
    return ".".join(path)


def wrap(text, width, size, family="sans"):
    max_chars = max(8, int(width / (size * CHAR_WIDTH[family])))
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            if line and len(line) + 1 + len(word) > max_chars:
                lines.append(line)
                line = word
            else:
                line = (line + " " + word).strip()
        lines.append(line)
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class Wireframe:
    def __init__(self, name, source):
        self.name, self.source = name, source
        self.items = []
        self.frames = []
        self._counter = 0

    def _id(self, prefix):
        self._counter += 1
        return "%s-%d" % (prefix, self._counter)

    # --- Modell -----------------------------------------------------
    def frame(self, label, x, y, w, h):
        fid = self._id("frame")
        self.frames.append(dict(id=fid, label=label, x=x, y=y, w=w, h=h))
        return fid

    def rect(self, x, y, w, h, fill="transparent", stroke=CHROME_STROKE, dashed=False, radius=0, frame=None):
        self.items.append(dict(kind="rect", id=self._id("rect"), x=x, y=y, w=w, h=h, fill=fill,
                               stroke=stroke, dashed=dashed, radius=radius, frame=frame))

    def line(self, x1, y1, x2, y2, stroke, dashed=False, width=1, frame=None):
        self.items.append(dict(kind="line", id=self._id("line"), x=x1, y=y1, dx=x2 - x1, dy=y2 - y1,
                               stroke=stroke, dashed=dashed, width=width, frame=frame))

    def text(self, x, y, text, size, line, color, width=None, bold=False, family="sans", frame=None):
        """Legt Text an (bei width umbrochen) und gibt Breite und Höhe zurück."""
        lines = wrap(text, width, size, family) if width else text.split("\n")
        factor = CHAR_WIDTH["sans-bold" if bold and family == "sans" else family]
        w = max(len(l) for l in lines) * size * factor
        h = len(lines) * line
        self.items.append(dict(kind="text", id=self._id("text"), x=x, y=y, w=w, h=h, lines=lines,
                               size=size, line=line, color=color, bold=bold, family=family, frame=frame))
        return w, h

    # --- Excalidraw -------------------------------------------------
    def _base(self, item_id, typ, x, y, w, h, **kw):
        seed = int(item_id.rsplit("-", 1)[1])
        d = dict(id=item_id, type=typ, x=x, y=y, width=w, height=h, angle=0,
                 strokeColor=CHROME_STROKE, backgroundColor="transparent", fillStyle="solid",
                 strokeWidth=1, strokeStyle="solid", roughness=0, opacity=100, groupIds=[],
                 frameId=None, roundness=None, seed=seed, version=1, versionNonce=seed,
                 isDeleted=False, boundElements=None, updated=1, link=None, locked=False)
        d.update(kw)
        return d

    def _excalidraw_item(self, it):
        if it["kind"] == "rect":
            return self._base(it["id"], "rectangle", it["x"], it["y"], it["w"], it["h"],
                              strokeColor=it["stroke"], backgroundColor=it["fill"],
                              strokeStyle="dashed" if it["dashed"] else "solid",
                              roundness={"type": 3, "value": it["radius"]} if it["radius"] else None,
                              frameId=it["frame"])
        if it["kind"] == "line":
            return self._base(it["id"], "line", it["x"], it["y"], abs(it["dx"]), abs(it["dy"]),
                              strokeColor=it["stroke"], strokeWidth=it["width"],
                              strokeStyle="dashed" if it["dashed"] else "solid",
                              points=[[0, 0], [it["dx"], it["dy"]]], lastCommittedPoint=None,
                              startBinding=None, endBinding=None, startArrowhead=None, endArrowhead=None,
                              frameId=it["frame"])
        text = "\n".join(it["lines"])
        return self._base(it["id"], "text", it["x"], it["y"], it["w"], it["h"], strokeColor=it["color"],
                          text=text, originalText=text, fontSize=it["size"],
                          fontFamily=EXCALIDRAW_FONT[it["family"]], textAlign="left", verticalAlign="top",
                          containerId=None, lineHeight=round(it["line"] / it["size"], 4), autoResize=True,
                          frameId=it["frame"])

    def to_excalidraw(self):
        elements = []
        for fr in self.frames:
            elements += [self._excalidraw_item(it) for it in self.items if it["frame"] == fr["id"]]
            elements.append(self._base(fr["id"], "frame", fr["x"], fr["y"], fr["w"], fr["h"], name=fr["label"],
                                       strokeColor="#bbbbbb"))
        elements += [self._excalidraw_item(it) for it in self.items if it["frame"] is None]
        return {"type": "excalidraw", "version": 2, "source": self.source, "elements": elements,
                "appState": {"viewBackgroundColor": CANVAS, "gridSize": None}, "files": {}}

    # --- SVG --------------------------------------------------------
    def _extent(self):
        boxes = [(f["x"], f["y"], f["w"], f["h"]) for f in self.frames]
        boxes += [(it["x"], it["y"], it.get("w", abs(it.get("dx", 0))), it.get("h", abs(it.get("dy", 0))))
                  for it in self.items]
        return (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[0] + b[2] for b in boxes), max(b[1] + b[3] for b in boxes))

    def _svg_item(self, it):
        if it["kind"] == "rect":
            return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s"%s/>' % (
                it["x"], it["y"], it["w"], it["h"], it["radius"],
                "none" if it["fill"] == "transparent" else it["fill"], it["stroke"],
                ' stroke-dasharray="8 6"' if it["dashed"] else "")
        if it["kind"] == "line":
            return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>' % (
                it["x"], it["y"], it["x"] + it["dx"], it["y"] + it["dy"], it["stroke"], it["width"],
                ' stroke-dasharray="8 6"' if it["dashed"] else "")
        out = ['<text font-family="%s" font-size="%s" fill="%s"%s>' % (
            SVG_FONT[it["family"]], it["size"], it["color"], ' font-weight="bold"' if it["bold"] else "")]
        for k, l in enumerate(it["lines"]):
            baseline = it["y"] + k * it["line"] + it["line"] / 2 + it["size"] * 0.35
            out.append('<tspan x="%s" y="%s">%s</tspan>' % (it["x"], round(baseline, 2), esc(l)))
        out.append("</text>")
        return "".join(out)

    def to_svg(self, margin=40):
        x0, y0, x1, y1 = self._extent()
        x0, y0, w, h = x0 - margin, y0 - margin - 24, x1 - x0 + 2 * margin, y1 - y0 + 2 * margin + 24
        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="%s %s %s %s">' % (
            w, h, x0, y0, w, h),
            '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (x0, y0, w, h, CANVAS)]
        for fr in self.frames:
            out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="#bbbbbb"/>' % (
                fr["x"], fr["y"], fr["w"], fr["h"]))
            out.append('<text x="%s" y="%s" font-family="%s" font-size="16" fill="%s">%s</text>' % (
                fr["x"], fr["y"] - 8, SVG_FONT["sans"], CHROME_TEXT, esc(fr["label"])))
        out += [self._svg_item(it) for it in self.items]
        out.append("</svg>")
        return "\n".join(out) + "\n"

    def write(self):
        base = os.path.join(WIREFRAME_DIR, self.name)
        with open(base + ".excalidraw", "w", encoding="utf-8") as f:
            json.dump(self.to_excalidraw(), f, ensure_ascii=False, indent=1)
            f.write("\n")
        with open(base + ".svg", "w", encoding="utf-8") as f:
            f.write(self.to_svg())

