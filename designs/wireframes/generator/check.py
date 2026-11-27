"""Prüft alle Wireframes in designs/wireframes/ gegen die Regeln aus designs/README.md.

Aufruf: python3 -I designs/wireframes/generator/check.py [Datei.excalidraw ...]
Ohne Argumente werden alle *.excalidraw-Dateien geprüft. Exit-Code 1 bei Verstößen.
Token-Namen stehen in Beschriftungen in geschweiften Klammern ({bg.page}), Fluent-Schlüssel ohne.
"""
import glob
import json
import os
import re
import sys

# -I nimmt das Skriptverzeichnis nicht in sys.path auf.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wirelib import TOKEN_REF, WIREFRAME_DIR, Tokens  # noqa: E402

FRAMES = {"Mobil": 320, "Tablet": 768, "Desktop": 1280}
FRAME_LABEL = re.compile(r"^(\S+) (\d+) px$")
STATES = ["Normal", "Laden", "Fehler", "Leer", "Ohne Berechtigung"]
HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b")


def check_bindings(elements, by_id, errors):
    for el in elements:
        refs = []
        if el.get("frameId"):
            refs.append(("frameId", el["frameId"]))
        if el.get("containerId"):
            refs.append(("containerId", el["containerId"]))
        for bound in el.get("boundElements") or []:
            refs.append(("boundElements", bound["id"]))
        for key in ("startBinding", "endBinding"):
            if el.get(key):
                refs.append((key, el[key]["elementId"]))
        for key, target in refs:
            if target not in by_id:
                errors.append("%s: %s verweist auf fehlendes Element %s" % (el["id"], key, target))
        if el.get("frameId") in by_id and by_id[el["frameId"]]["type"] != "frame":
            errors.append("%s: frameId %s ist kein Rahmen" % (el["id"], el["frameId"]))
        if el.get("containerId") in by_id:
            container = by_id[el["containerId"]]
            if not any(b["id"] == el["id"] for b in container.get("boundElements") or []):
                errors.append("%s: Container %s führt den Text nicht in boundElements" % (el["id"], container["id"]))


def check_frames(elements, errors):
    frames = [el for el in elements if el["type"] == "frame"]
    found = {}
    for fr in frames:
        match = FRAME_LABEL.match(fr.get("name") or "")
        if not match or FRAMES.get(match.group(1)) != int(match.group(2)):
            errors.append("Rahmen %s: Beschriftung %r passt nicht zu %s" % (fr["id"], fr.get("name"), FRAMES))
            continue
        if fr["width"] != int(match.group(2)):
            errors.append("Rahmen %r: Breite %s statt %s" % (fr["name"], fr["width"], match.group(2)))
        found[match.group(1)] = fr
    for name in FRAMES:
        if name not in found:
            errors.append("Rahmen %s %s px fehlt" % (name, FRAMES[name]))
    for name, fr in found.items():
        texts = " ".join(el["text"] for el in elements if el["type"] == "text" and el.get("frameId") == fr["id"])
        for state in STATES:
            if state not in texts:
                errors.append("Rahmen %r: Zustand %r weder gezeichnet noch vermerkt" % (fr["name"], state))


def check_texts(elements, tokens, errors):
    labels = [(el["id"], el.get("text", "")) for el in elements if el["type"] == "text"]
    labels += [(el["id"], el.get("name") or "") for el in elements if el["type"] == "frame"]
    for el_id, text in labels:
        for hex_value in HEX.findall(text):
            errors.append("%s: Hex-Wert %s in Beschriftung" % (el_id, hex_value))
        for name in TOKEN_REF.findall(text):
            if name not in tokens.names:
                errors.append("%s: Token {%s} fehlt in tokens.json" % (el_id, name))


def check_file(path, tokens):
    errors = []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return ["kein gültiges JSON: %s" % exc]
    elements = [el for el in data.get("elements", []) if not el.get("isDeleted")]
    by_id = {}
    for el in elements:
        if el["id"] in by_id:
            errors.append("doppelte id %s" % el["id"])
        by_id[el["id"]] = el
    check_bindings(elements, by_id, errors)
    check_frames(elements, errors)
    check_texts(elements, tokens, errors)
    svg = os.path.splitext(path)[0] + ".svg"
    if not os.path.exists(svg):
        errors.append("SVG-Export %s fehlt" % os.path.basename(svg))
    return errors


def main(argv):
    paths = argv or sorted(glob.glob(os.path.join(WIREFRAME_DIR, "*.excalidraw")))
    if not paths:
        print("keine Wireframes gefunden")
        return 0
    tokens = Tokens()
    failed = False
    for path in paths:
        errors = check_file(path, tokens)
        name = os.path.relpath(path)
        if errors:
            failed = True
            print("FEHLER %s" % name)
            for err in errors:
                print("  - " + err)
        else:
            print("ok     %s" % name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
