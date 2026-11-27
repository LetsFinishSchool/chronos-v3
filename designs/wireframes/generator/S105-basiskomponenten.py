"""Wireframe der Basiskomponenten des Design-Systems zu Ticket 105 (Task 119).

Dieses Skript ist die Quelle von S105-basiskomponenten.excalidraw und S105-basiskomponenten.svg.
Wird die Excalidraw-Datei im Editor von Hand bearbeitet, dieses Skript danach nicht mehr ausführen:
Es überschreibt beide Dateien und die Handarbeit geht verloren.

Aufruf: python3 -I designs/wireframes/generator/S105-basiskomponenten.py
"""
import os
import sys

# -I nimmt das Skriptverzeichnis nicht in sys.path auf.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wirelib import (ANNOTATION_TEXT, CHROME_STROKE, CHROME_TEXT, Tokens, Wireframe,  # noqa: E402
                     measure_text)

T = Tokens()

MIN_TARGET = 24  # K-012 Regel 6
FOCUS_RING_WIDTH = 2  # K-012 Regel 4
FOCUS_GAP = 2

BREAKPOINTS = [
    dict(name="Mobil", width=320, range="Mobil", side="space.4"),
    dict(name="Tablet", width=T.px("breakpoint.tablet"), range="Tablet ab {breakpoint.tablet}", side="space.8"),
    dict(name="Desktop", width=T.px("breakpoint.desktop"), range="Desktop ab {breakpoint.desktop}",
         side="space.12"),
]

CAPTION_HEIGHT = 32
SPECIMEN_LABEL_SIZE = 12
SPECIMEN_LABEL_LINE = 16
ANNOTATION_GAP = 24
ANNOTATION_WIDTH = 440
FRAME_GAP = 48
FRAME_PADDING = 16
NOTE_SIZE = 14
NOTE_LINE = 20
NOTE_PADDING = 8
SECTION_GAP = 32
CANVAS_WIDTH = sum(bp["width"] for bp in BREAKPOINTS) + 3 * (ANNOTATION_GAP + ANNOTATION_WIDTH) + 2 * FRAME_GAP


class Pen:
    """Zeichnet in einen Rahmen oder misst nur (wf ist None)."""

    def __init__(self, wf=None, frame=None):
        self.wf, self.frame = wf, frame

    def rect(self, x, y, w, h, fill="transparent", stroke=CHROME_STROKE, radius=0, stroke_width=1):
        if self.wf:
            self.wf.rect(x, y, w, h, fill=fill, stroke=stroke, radius=radius, frame=self.frame,
                         stroke_width=stroke_width)

    def ellipse(self, x, y, w, h, fill="transparent", stroke=CHROME_STROKE, stroke_width=1):
        if self.wf:
            self.wf.ellipse(x, y, w, h, fill=fill, stroke=stroke, frame=self.frame, stroke_width=stroke_width)

    def line(self, x1, y1, x2, y2, stroke, width=1):
        if self.wf:
            self.wf.line(x1, y1, x2, y2, stroke, width=width, frame=self.frame)

    def text(self, x, y, text, style, color, width=None):
        s = T.type_style(style)
        if self.wf:
            return self.wf.text(x, y, text, s["size"], s["line"], T.color(color), width=width, bold=s["bold"],
                                frame=self.frame)
        _, w, h = measure_text(text, s["size"], s["line"], width, s["bold"])
        return w, h

    def label(self, x, y, text, width):
        if self.wf:
            return self.wf.text(x, y, text, SPECIMEN_LABEL_SIZE, SPECIMEN_LABEL_LINE, CHROME_TEXT, width=width,
                                frame=self.frame)
        _, w, h = measure_text(text, SPECIMEN_LABEL_SIZE, SPECIMEN_LABEL_LINE, width)
        return w, h

    def centered(self, x, y, w, h, text, style, color):
        tw, th = Pen().text(0, 0, text, style, color)
        return self.text(x + (w - tw) / 2, y + (h - th) / 2, text, style, color)

    def cross(self, cx, cy, half, color, width=2):
        self.line(cx - half, cy - half, cx + half, cy + half, color, width=width)
        self.line(cx - half, cy + half, cx + half, cy - half, color, width=width)

    def check(self, cx, cy, half, color, width=2):
        self.line(cx - half, cy, cx - half / 3, cy + half * 2 / 3, color, width=width)
        self.line(cx - half / 3, cy + half * 2 / 3, cx + half, cy - half * 2 / 3, color, width=width)

    def chevron(self, cx, cy, half, color, width=2):
        self.line(cx - half, cy - half / 2, cx, cy + half / 2, color, width=width)
        self.line(cx, cy + half / 2, cx + half, cy - half / 2, color, width=width)


class Specimen:
    """Ein gezeichnetes Beispiel mit Beschriftung darunter; draw(pen, x, y) gibt (Breite, Höhe) zurück."""

    def __init__(self, label, draw):
        self.label, self.draw = label, draw
        self.w, self.h = draw(Pen(), 0, 0)
        _, self.label_h = Pen().label(0, 0, label, self.w)
        self.total_h = self.h + T.px("space.1") + self.label_h


class Section:
    def __init__(self, title, specimens, notes, full_width=False):
        self.title, self.specimens, self.notes, self.full_width = title, specimens, notes, full_width


def annotation_height(notes):
    _, _, h = measure_text("\n".join("· " + n for n in notes), NOTE_SIZE, NOTE_LINE, ANNOTATION_WIDTH)
    return h


def flow(specimens, width):
    """Ordnet Beispiele zeilenweise an; gibt Positionen und Gesamthöhe zurück."""
    gap_x, gap_y = T.px("space.4"), T.px("space.6")
    positions, x, y, row_h = [], 0, 0, 0
    for sp in specimens:
        if x and x + sp.w > width:
            x, y, row_h = 0, y + row_h + gap_y, 0
        positions.append((x, y))
        x += sp.w + gap_x
        row_h = max(row_h, sp.total_h)
    return positions, y + row_h


def section_height(section, bp):
    side = T.px(bp["side"])
    inner = bp["width"] if section.full_width else bp["width"] - 2 * side
    _, h = flow(section.specimens, inner)
    pad = T.px("space.4") if section.full_width else T.px("space.6")
    return max(h + 2 * pad, annotation_height(section.notes) + 2 * NOTE_PADDING)


def draw_section(wf, frame, bp, section, x, y):
    side = T.px(bp["side"])
    inner = bp["width"] if section.full_width else bp["width"] - 2 * side
    left = x if section.full_width else x + side
    pad = T.px("space.4") if section.full_width else T.px("space.6")
    height = section_height(section, bp)
    wf.text(x + FRAME_PADDING, y, section.title, 16, CAPTION_HEIGHT, CHROME_TEXT, frame=frame)
    top = y + CAPTION_HEIGHT
    wf.rect(x, top, bp["width"], height, fill=T.color("bg.page"), frame=frame)
    positions, _ = flow(section.specimens, inner)
    pen = Pen(wf, frame)
    for sp, (px, py) in zip(section.specimens, positions):
        sx, sy = left + px, top + pad + py
        sp.draw(pen, sx, sy)
        pen.label(sx, sy + sp.h + T.px("space.1"), sp.label, sp.w)
    notes = ["%s: Seite {bg.page}; seitlicher Rand {%s}" % (bp["range"], bp["side"])] + section.notes
    wf.text(x + bp["width"] + ANNOTATION_GAP, top, "\n".join("· " + n for n in notes), NOTE_SIZE, NOTE_LINE,
            ANNOTATION_TEXT, width=ANNOTATION_WIDTH)
    return CAPTION_HEIGHT + height + SECTION_GAP


# --- Button -----------------------------------------------------------

BUTTON_VARIANTS = [
    dict(name="primär", key="button.save", sample="Speichern", fill="brand.primary", border=None,
         text="text.on-brand"),
    dict(name="sekundär", key="button.cancel", sample="Abbrechen", fill="bg.surface", border="border.brand",
         text="text.brand"),
    dict(name="Gefahr", key="button.delete", sample="Löschen", fill="status.danger", border=None,
         text="text.on-brand"),
]
BUTTON_STATES = ["normal", "Fokus", "deaktiviert", "laden"]
BUTTON_LOADING = ("button.loading", "Lädt …")
BUTTON_STYLE = "body-m-semibold"


def button_size(label):
    style = T.type_style(BUTTON_STYLE)
    w, _ = Pen().text(0, 0, label, BUTTON_STYLE, "text.primary")
    h = style["line"] + 2 * T.px("space.2")
    assert h >= MIN_TARGET
    return w + 2 * T.px("space.4"), h


def draw_button(variant, state):
    label = BUTTON_LOADING[1] if state == "laden" else variant["sample"]

    def draw(pen, x, y):
        w, h = button_size(label)
        disabled = state == "deaktiviert"
        fill = "bg.muted" if disabled else variant["fill"]
        border = "border.default" if disabled else variant["border"]
        text = "text.muted" if disabled else variant["text"]
        pen.rect(x, y, w, h, fill=T.color(fill), stroke=T.color(border or fill), radius=T.px("radius.md"))
        pen.centered(x, y, w, h, label, BUTTON_STYLE, text)
        if state == "Fokus":
            ring = FOCUS_GAP + FOCUS_RING_WIDTH / 2
            pen.rect(x - ring, y - ring, w + 2 * ring, h + 2 * ring, stroke=T.color("focus.ring"),
                     radius=T.px("radius.md") + ring, stroke_width=FOCUS_RING_WIDTH)
        return w, h
    return draw


def button_section():
    specimens = [Specimen("%s · %s" % (v["name"], s), draw_button(v, s))
                 for v in BUTTON_VARIANTS for s in BUTTON_STATES]
    notes = [
        "Höhe 40 px = Zeile {typography.style.body-m-semibold} + 2 × {space.2}, innen seitlich {space.4},"
        " Ecken {radius.md}; Zielgröße mindestens 24 × 24 px (K-012 Regel 6).",
        "primär button.save „Speichern“: Fläche {brand.primary}, Text {text.on-brand}.",
        "sekundär button.cancel „Abbrechen“: Fläche {bg.surface}, Rahmen {border.brand}, Text {text.brand}.",
        "Gefahr button.delete „Löschen“: Fläche {status.danger}, Text {text.on-brand}.",
        "Fokus: 2 px Rahmen {focus.ring} im Abstand 2 px, nie verdeckt (K-012 Regel 4).",
        "deaktiviert: Fläche {bg.muted}, Text {text.muted}, Rahmen {border.default}; ohne Fokus, ohne Klick.",
        "laden button.loading „Lädt …“: Farben wie normal, Klick ohne Wirkung (aria-busy), kein Spinner.",
    ]
    return Section("Button", specimens, notes)


# --- Badge ------------------------------------------------------------

BADGE_VARIANTS = [
    dict(name="neutral", key="badge.neutral", sample="Entwurf", fill="bg.muted", text="text.secondary"),
    dict(name="Marke", key="badge.brand", sample="Neu", fill="bg.brand-subtle", text="text.brand"),
    dict(name="Erfolg", key="badge.success", sample="Zugesagt", fill="bg.success-subtle", text="text.success"),
    dict(name="Warnung", key="badge.warning", sample="Ausstehend", fill="bg.warning-subtle",
         text="text.warning"),
    dict(name="Gefahr", key="badge.danger", sample="Abgesagt", fill="bg.danger-subtle", text="text.danger"),
]
BADGE_STYLE = "body-s-semibold"


def draw_badge(variant):
    def draw(pen, x, y):
        tw, th = Pen().text(0, 0, variant["sample"], BADGE_STYLE, variant["text"])
        w, h = tw + 2 * T.px("space.3"), th + 2 * T.px("space.1")
        pen.rect(x, y, w, h, fill=T.color(variant["fill"]), stroke=T.color(variant["fill"]),
                 radius=T.px("radius.full"))
        pen.text(x + T.px("space.3"), y + T.px("space.1"), variant["sample"], BADGE_STYLE, variant["text"])
        return w, h
    return draw


def badge_section():
    specimens = [Specimen(v["name"], draw_badge(v)) for v in BADGE_VARIANTS]
    notes = [
        "Rundung {radius.full}, innen {space.1} oben und unten, {space.3} seitlich, Schrift"
        " {typography.style.body-s-semibold}. Nicht bedienbar.",
        "Immer mit Text; die Farbe trägt nie allein die Bedeutung (K-012 Regel 2).",
        "neutral badge.neutral „Entwurf“: Fläche {bg.muted}, Text {text.secondary}.",
        "Marke badge.brand „Neu“: Fläche {bg.brand-subtle}, Text {text.brand}.",
        "Erfolg badge.success „Zugesagt“: Fläche {bg.success-subtle}, Text {text.success}.",
        "Warnung badge.warning „Ausstehend“: Fläche {bg.warning-subtle}, Text {text.warning}.",
        "Gefahr badge.danger „Abgesagt“: Fläche {bg.danger-subtle}, Text {text.danger}.",
    ]
    return Section("Badge", specimens, notes)


# --- Gesamtbild -------------------------------------------------------

def sections():
    return [button_section(), badge_section()]


STORY_STATES = [
    "Normal: bei jeder Komponente gezeichnet.",
    "Laden: Button (laden) und Liste (laden).",
    "Fehler: Alert (Fehler) und Eingabefelder (Fehler mit Fehlermeldung).",
    "Leer: Liste (leer mit Leertext); sonst nicht zutreffend, die Komponenten zeigen selbst keine Daten.",
    "Ohne Berechtigung: nicht zutreffend. Basiskomponenten kennen keine Berechtigung; die Seite entscheidet,"
    " ob sie eine Komponente zeigt.",
]

CANVAS_NOTES = [
    "Farben, Abstände, Radien und Schriftstile als Token-Namen aus designs/tokens/tokens.json in geschweiften"
    " Klammern. Texte als Fluent-Schlüssel mit Beispieltext (ADR-010). Füllfarben zeigen den hellen Modus;"
    " der dunkle nutzt dieselben Namen.",
    "Alle Komponenten erscheinen in jedem Rahmen. Layoutstufen: Mobil ab 320 px, Tablet ab {breakpoint.tablet},"
    " Desktop ab {breakpoint.desktop}.",
]


def draw_breakpoint(wf, bp, x, y, section_list):
    states_text = "\n".join(STORY_STATES)
    states_h = measure_text(states_text, NOTE_SIZE, NOTE_LINE, bp["width"] - 2 * FRAME_PADDING)[2] \
        + 2 * NOTE_PADDING
    heights = [CAPTION_HEIGHT + section_height(s, bp) + SECTION_GAP for s in section_list]
    frame_h = FRAME_PADDING + sum(heights) + states_h + FRAME_PADDING
    frame = wf.frame("%s %d px" % (bp["name"], bp["width"]), x, y, bp["width"], frame_h)
    row_y = y + FRAME_PADDING
    for section in section_list:
        row_y += draw_section(wf, frame, bp, section, x, row_y)
    wf.rect(x + FRAME_PADDING / 2, row_y, bp["width"] - FRAME_PADDING, states_h, dashed=True, frame=frame)
    wf.text(x + FRAME_PADDING, row_y + NOTE_PADDING, states_text, NOTE_SIZE, NOTE_LINE, CHROME_TEXT,
            width=bp["width"] - 2 * FRAME_PADDING, frame=frame)


def main():
    wf = Wireframe("S105-basiskomponenten", "chronos-v3/designs/wireframes/generator/S105-basiskomponenten.py")
    wf.text(0, 0, "S105 Basiskomponenten: Wireframe zu Ticket 105 (Task 119)", 28, 36, CHROME_TEXT)
    y = 44
    for note in CANVAS_NOTES:
        _, h = wf.text(0, y, note, 15, 22, ANNOTATION_TEXT, width=CANVAS_WIDTH)
        y += h + 6
    x, y = 0, y + 56
    section_list = sections()
    for bp in BREAKPOINTS:
        draw_breakpoint(wf, bp, x, y, section_list)
        x += bp["width"] + ANNOTATION_GAP + ANNOTATION_WIDTH + FRAME_GAP
    wf.write()


if __name__ == "__main__":
    main()
