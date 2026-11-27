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


# --- Alert ------------------------------------------------------------

SYMBOL_SIZE = 24  # Platzhalter, es gibt keinen Symbolsatz
ALERT_VARIANTS = [
    dict(name="Info", key="alert.info", sample="Der Termin wurde verschoben.", symbol="info",
         fill="bg.brand-subtle", border="border.brand", text="text.info"),
    dict(name="Erfolg", key="alert.success", sample="Die Rückmeldung ist gespeichert.", symbol="check",
         fill="bg.success-subtle", border="border.success", text="text.success"),
    dict(name="Warnung", key="alert.warning", sample="Es fehlen noch Rückmeldungen.", symbol="warning",
         fill="bg.warning-subtle", border="border.default", text="text.warning"),
    dict(name="Fehler", key="alert.error", sample="Die Rückmeldung konnte nicht gespeichert werden.",
         symbol="error", fill="bg.danger-subtle", border="border.danger", text="text.danger"),
]
CLOSE_KEY = ("alert.close", "Schließen")


def content_width(bp):
    return min(bp["width"] - 2 * T.px(bp["side"]), T.px("size.text-max"))


def draw_symbol(pen, x, y, kind, color):
    c = T.color(color)
    pen.ellipse(x, y, SYMBOL_SIZE, SYMBOL_SIZE, stroke=c, stroke_width=2)
    cx, cy = x + SYMBOL_SIZE / 2, y + SYMBOL_SIZE / 2
    if kind == "check":
        pen.check(cx, cy, 5, c)
    elif kind == "error":
        pen.cross(cx, cy, 4, c)
    else:
        pen.centered(x, y, SYMBOL_SIZE, SYMBOL_SIZE, "i" if kind == "info" else "!", "body-s-semibold", color)


def draw_alert(variant, closable, width):
    def draw(pen, x, y):
        pad, gap = T.px("space.4"), T.px("space.3")
        close_size = T.px("space.10")
        assert close_size >= MIN_TARGET
        text_w = width - 2 * pad - SYMBOL_SIZE - gap - ((close_size + gap) if closable else 0)
        _, text_h = Pen().text(0, 0, variant["sample"], "body-m-regular", "text.primary", width=text_w)
        h = max(text_h + 2 * pad, close_size + 2 * T.px("space.2") if closable else 0)
        pen.rect(x, y, width, h, fill=T.color(variant["fill"]), stroke=T.color(variant["border"]),
                 radius=T.px("radius.md"))
        draw_symbol(pen, x + pad, y + pad, variant["symbol"], variant["text"])
        pen.text(x + pad + SYMBOL_SIZE + gap, y + pad, variant["sample"], "body-m-regular", "text.primary",
                 width=text_w)
        if closable:
            bx, by = x + width - T.px("space.2") - close_size, y + T.px("space.2")
            pen.rect(bx, by, close_size, close_size, stroke=T.color("border.control"), radius=T.px("radius.md"))
            pen.cross(bx + close_size / 2, by + close_size / 2, 5, T.color("text.secondary"))
        return width, h
    return draw


def alert_section(bp):
    width = content_width(bp)
    specimens = [Specimen("%s · %s" % (v["name"], "mit Schließen" if c else "ohne Schließen"),
                          draw_alert(v, c, width)) for v in ALERT_VARIANTS for c in (True, False)]
    notes = [
        "Breite höchstens {size.text-max}; Innenabstand {space.4}, Abstand Symbol–Text {space.3},"
        " Ecken {radius.md}, Rahmen 1 px, Text {typography.style.body-m-regular} in {text.primary}.",
        "Symbol und Text tragen die Bedeutung, nie die Farbe allein (K-012 Regel 2). Das Symbol ist ein"
        " Platzhalter (24 px); ein Symbolsatz ist nicht festgelegt.",
        "Info alert.info: Fläche {bg.brand-subtle}, Rahmen {border.brand}, Symbol {text.info}."
        " Es gibt kein bg.info-subtle und kein border.info; die Fläche ist ein Ersatz (siehe Anmerkungen oben).",
        "Erfolg alert.success: Fläche {bg.success-subtle}, Rahmen {border.success}, Symbol {text.success}.",
        "Warnung alert.warning: Fläche {bg.warning-subtle}, Rahmen {border.default}, Symbol {text.warning}."
        " Es gibt kein border.warning.",
        "Fehler alert.error: Fläche {bg.danger-subtle}, Rahmen {border.danger}, Symbol {text.danger}.",
        "Schließen-Button alert.close „Schließen“ (Beschriftung für Screenreader): %d × %d px ({space.10}),"
        " Rahmen {border.control}, Kreuz {text.secondary}. Fokus wie beim Button."
        % (T.px("space.10"), T.px("space.10")),
    ]
    return Section("Alert", specimens, notes)


# --- Karte ------------------------------------------------------------

CARD_TITLE = ("card.title", "Probe am Samstag")
CARD_TEXT = ("card.text", "Beginn um 10:00 Uhr im Gemeindehaus. Bitte bis Donnerstag zu- oder absagen.")


def draw_card(with_action, width):
    def draw(pen, x, y):
        pad, gap = T.px("space.4"), T.px("space.2")
        inner = width - 2 * pad
        _, title_h = pen.text(0, 0, CARD_TITLE[1], "heading-h3", "text.primary", width=inner)
        _, text_h = pen.text(0, 0, CARD_TEXT[1], "body-m-regular", "text.secondary", width=inner)
        action = button_size(BUTTON_VARIANTS[1]["sample"]) if with_action else None
        h = 2 * pad + title_h + gap + text_h + ((T.px("space.4") + action[1]) if action else 0)
        pen.rect(x, y, width, h, fill=T.color("bg.surface"), stroke=T.color("border.default"),
                 radius=T.px("radius.lg"))
        cy = y + pad
        pen.text(x + pad, cy, CARD_TITLE[1], "heading-h3", "text.primary", width=inner)
        cy += title_h + gap
        pen.text(x + pad, cy, CARD_TEXT[1], "body-m-regular", "text.secondary", width=inner)
        if action:
            draw_button(BUTTON_VARIANTS[1], "normal")(pen, x + pad, cy + text_h + T.px("space.4"))
        return width, h
    return draw


def card_section(bp):
    width = content_width(bp)
    specimens = [Specimen("ohne Aktion", draw_card(False, width)), Specimen("mit Aktion", draw_card(True, width))]
    notes = [
        "Breite höchstens {size.text-max}; Fläche {bg.surface}, Rahmen {border.default}, Ecken {radius.lg},"
        " Innenabstand {space.4}, Schatten {shadow.sm} (im Wireframe nicht gezeichnet).",
        "Titel card.title „Probe am Samstag“: {typography.style.heading-h3}, {text.primary}.",
        "Inhalt card.text: {typography.style.body-m-regular}, {text.secondary}; Abstand zum Titel {space.2}.",
        "Aktion (optional): Button sekundär, Abstand zum Inhalt {space.4}. Die Karte selbst ist nicht anklickbar.",
        "Leer, laden, Fehler: nicht zutreffend, die Karte zeigt den Inhalt, den die Seite ihr gibt.",
    ]
    return Section("Karte", specimens, notes)


# --- Liste ------------------------------------------------------------

LIST_ITEMS = [("Probe am Samstag", "Sa, 5. Dezember, 10:00"), ("Leitungsrunde", "Di, 8. Dezember, 19:30"),
              ("Aufbau Sommerfest", "Fr, 11. Dezember, 17:00")]
LIST_EMPTY = ("list.empty", "Keine Einträge.")
LIST_LOADING = ("list.loading", "Lädt …")


def draw_list(kind, width):
    def draw(pen, x, y):
        pad = T.px("space.4")
        row_h = T.px("space.2") * 2 + 24 + 20
        if kind == "normal":
            h = row_h * len(LIST_ITEMS)
        elif kind == "leer":
            h = 2 * pad + 24
        else:
            h = 2 * pad + 20 + 2 * (T.px("space.4") + T.px("space.3")) + T.px("space.2")
        pen.rect(x, y, width, h, fill=T.color("bg.surface"), stroke=T.color("border.default"),
                 radius=T.px("radius.lg"))
        if kind == "normal":
            for i, (title, meta) in enumerate(LIST_ITEMS):
                top = y + i * row_h
                if i:
                    pen.line(x, top, x + width, top, T.color("border.default"))
                pen.text(x + pad, top + T.px("space.2"), title, "body-m-regular", "text.primary")
                pen.text(x + pad, top + T.px("space.2") + 24, meta, "body-s-regular", "text.secondary")
        elif kind == "leer":
            pen.text(x + pad, y + pad, LIST_EMPTY[1], "body-m-regular", "text.muted")
        else:
            pen.text(x + pad, y + pad, LIST_LOADING[1], "body-s-regular", "text.muted")
            bar_y = y + pad + 20 + T.px("space.2")
            for w_factor in (0.7, 0.5):
                bar_h = T.px("space.4")
                pen.rect(x + pad, bar_y, (width - 2 * pad) * w_factor, bar_h, fill=T.color("bg.muted"),
                         stroke=T.color("bg.muted"), radius=T.px("radius.md"))
                bar_y += bar_h + T.px("space.3")
        return width, h
    return draw


def list_section(bp):
    width = content_width(bp)
    specimens = [Specimen("normal", draw_list("normal", width)), Specimen("leer", draw_list("leer", width)),
                 Specimen("laden", draw_list("laden", width))]
    notes = [
        "Breite höchstens {size.text-max}; Fläche {bg.surface}, Rahmen {border.default}, Ecken {radius.lg},"
        " Trenner {border.default}, Zeilenabstand oben und unten {space.2}, seitlich {space.4}.",
        "normal: Zeile mit Titel ({typography.style.body-m-regular}, {text.primary}) und Angabe"
        " ({typography.style.body-s-regular}, {text.secondary}).",
        "leer list.empty „Keine Einträge.“: {typography.style.body-m-regular}, {text.muted}.",
        "laden list.loading „Lädt …“ (role=status): {typography.style.body-s-regular}, {text.muted}; darunter"
        " Platzhalterbalken in {bg.muted}. Kein Spinner.",
        "Fehler, ohne Berechtigung: nicht zutreffend; die Seite zeigt dafür einen Alert statt der Liste.",
    ]
    return Section("Liste", specimens, notes)


# --- Eingabefelder ----------------------------------------------------

FIELD_STATES = ["normal", "mit Hinweistext", "Fokus", "deaktiviert", "Fehler"]
FIELD_KINDS = [
    dict(kind="text", name="Textfeld", label="Name", value="Vor- und Nachname",
         hint="Wird in der Teamliste angezeigt.", error="Bitte einen Namen eingeben."),
    dict(kind="textarea", name="Textbereich", label="Notiz", value="Notiz hinzufügen",
         hint="Höchstens 500 Zeichen.", error="Die Notiz ist zu lang."),
    dict(kind="checkbox", name="Checkbox", label="Erinnerung per E-Mail", value=None,
         hint="Einen Tag vor dem Termin.", error="Bitte bestätigen."),
    dict(kind="radio", name="Radiogruppe", label="Rückmeldung", value=("Zusagen", "Absagen"),
         hint="Gilt für diesen Termin.", error="Bitte eine Antwort wählen."),
    dict(kind="select", name="Auswahl", label="Gruppe", value="Bitte wählen",
         hint="Bestimmt, wer den Termin sieht.", error="Bitte eine Gruppe wählen."),
]
CONTROL_HEIGHT = T.px("space.10")
TEXTAREA_HEIGHT = T.px("space.20") + T.px("space.2") * 2
CHOICE_SIZE = 24
FIELD_WIDTH = T.px("size.text-max") // 2


def field_width(bp):
    return min(bp["width"] - 2 * T.px(bp["side"]), FIELD_WIDTH)


def draw_control_box(pen, x, y, w, h, state):
    """Rahmen eines Eingabefelds nach Zustand; Fokus und Fehler nach K-012 Regeln 3 und 4."""
    disabled = state == "deaktiviert"
    error = state == "Fehler"
    pen.rect(x, y, w, h, fill=T.color("bg.muted"),
             stroke=T.color("border.default" if disabled else "border.danger" if error else "border.control"),
             radius=T.px("radius.md"), stroke_width=2 if error else 1)
    if state == "Fokus":
        ring = FOCUS_GAP + FOCUS_RING_WIDTH / 2
        pen.rect(x - ring, y - ring, w + 2 * ring, h + 2 * ring, stroke=T.color("focus.ring"),
                 radius=T.px("radius.md") + ring, stroke_width=FOCUS_RING_WIDTH)


def draw_choice(pen, x, y, round_, selected, state):
    color = "border.default" if state == "deaktiviert" else "border.danger" if state == "Fehler" else "border.control"
    width = 2 if state == "Fehler" else 1
    if round_:
        pen.ellipse(x, y, CHOICE_SIZE, CHOICE_SIZE, fill=T.color("bg.surface"), stroke=T.color(color),
                    stroke_width=width)
        if selected:
            dot = T.px("space.3")
            pen.ellipse(x + (CHOICE_SIZE - dot) / 2, y + (CHOICE_SIZE - dot) / 2, dot, dot,
                        fill=T.color("brand.primary"), stroke=T.color("brand.primary"))
    else:
        pen.rect(x, y, CHOICE_SIZE, CHOICE_SIZE, fill=T.color("bg.surface"), stroke=T.color(color),
                 radius=T.px("radius.md") / 2, stroke_width=width)
    if state == "Fokus":
        ring = FOCUS_GAP + FOCUS_RING_WIDTH / 2
        if round_:
            pen.ellipse(x - ring, y - ring, CHOICE_SIZE + 2 * ring, CHOICE_SIZE + 2 * ring,
                        stroke=T.color("focus.ring"), stroke_width=FOCUS_RING_WIDTH)
        else:
            pen.rect(x - ring, y - ring, CHOICE_SIZE + 2 * ring, CHOICE_SIZE + 2 * ring,
                     stroke=T.color("focus.ring"), radius=T.px("radius.md") / 2 + ring,
                     stroke_width=FOCUS_RING_WIDTH)


def draw_message(pen, x, y, width, spec, state):
    """Hinweis- oder Fehlertext unter dem Feld; gibt die Höhe zurück (0 ohne Text)."""
    if state == "mit Hinweistext":
        return pen.text(x, y, spec["hint"], "body-s-regular", "text.secondary", width=width)[1]
    if state == "Fehler":
        pen.ellipse(x, y + 2, 16, 16, stroke=T.color("text.danger"), stroke_width=2)
        pen.cross(x + 8, y + 10, 3, T.color("text.danger"), width=2)
        return pen.text(x + 16 + T.px("space.2"), y, spec["error"], "body-s-regular", "text.danger",
                        width=width - 16 - T.px("space.2"))[1]
    return 0


def draw_field(spec, state, width):
    gap = T.px("space.1")
    value_color = "text.muted"

    def draw(pen, x, y):
        disabled = state == "deaktiviert"
        label_color = "text.muted" if disabled else "text.primary"
        cy = y
        if spec["kind"] in ("text", "textarea", "select"):
            cy += pen.text(x, cy, spec["label"], "body-s-semibold", label_color)[1] + gap
            h = TEXTAREA_HEIGHT if spec["kind"] == "textarea" else CONTROL_HEIGHT
            draw_control_box(pen, x, cy, width, h, state)
            pen.text(x + T.px("space.3"), cy + (T.px("space.2") if spec["kind"] == "textarea" else
                                                (h - 24) / 2), spec["value"], "body-m-regular", value_color)
            if spec["kind"] == "select":
                pen.chevron(x + width - T.px("space.5"), cy + h / 2, 5, T.color("text.secondary" if not disabled
                                                                                 else "text.muted"))
            cy += h
        elif spec["kind"] == "checkbox":
            draw_choice(pen, x, cy, False, False, state)
            pen.text(x + CHOICE_SIZE + T.px("space.2"), cy, spec["label"], "body-m-regular", label_color)
            cy += CHOICE_SIZE
        else:
            cy += pen.text(x, cy, spec["label"], "body-s-semibold", label_color)[1] + gap
            for i, option in enumerate(spec["value"]):
                draw_choice(pen, x, cy, True, i == 0, state)
                pen.text(x + CHOICE_SIZE + T.px("space.2"), cy, option, "body-m-regular", label_color)
                cy += CHOICE_SIZE + T.px("space.2")
            cy -= T.px("space.2")
        message_h = draw_message(pen, x, cy + gap, width, spec, state)
        if message_h:
            cy += gap + message_h
        return width, cy - y
    return draw


def field_section(bp):
    width = field_width(bp)
    specimens = [Specimen("%s · %s" % (k["name"], s), draw_field(k, s, width))
                 for k in FIELD_KINDS for s in FIELD_STATES]
    notes = [
        "Feldbreite die Hälfte von {size.text-max} (288 px), auf Mobil die volle Spaltenbreite."
        " Kein Breitentoken vorhanden.",
        "Feld: Fläche {bg.muted}, Rahmen {border.control}, Ecken {radius.md}, Höhe 40 px ({space.10})."
        " Beschriftung oben ({typography.style.body-s-semibold}, {text.primary}), Abstand {space.1};"
        " Platzhalter {typography.style.body-m-regular} in {text.muted}.",
        "Textfeld field.text.label „Name“, Textbereich field.textarea.label „Notiz“ (Höhe 96 px), Auswahl"
        " field.select.label „Gruppe“ mit Pfeil {text.secondary}.",
        "Checkbox und Radio: 24 × 24 px, Fläche {bg.surface}, Rahmen {border.control}; gewählt: Punkt"
        " {brand.primary}. Die Zeile ist inklusive Beschriftung klickbar.",
        "Hinweistext field.*.hint: {typography.style.body-s-regular}, {text.secondary}, Abstand {space.1}.",
        "Fokus: 2 px Rahmen {focus.ring} im Abstand 2 px (K-012 Regel 4), Rahmen {border.control} bleibt.",
        "deaktiviert: Rahmen {border.default}, Beschriftung {text.muted}; nicht fokussierbar.",
        "Fehler: Rahmen {border.danger} 2 px, darunter Symbol und Fehlermeldung field.*.error in"
        " {text.danger}; Farbe nie allein (K-012 Regel 2).",
        "Hinweistext und Fehlermeldung hängen per aria-describedby am Feld. Schalter und Auswahlkacheln"
        " sind nicht Teil dieses Wireframes.",
    ]
    return Section("Eingabefelder", specimens, notes)


# --- Dialog -----------------------------------------------------------

DIALOG_TITLE = ("dialog.title", "Termin absagen?")
DIALOG_BUTTONS = [dict(BUTTON_VARIANTS[1], key="dialog.cancel", sample="Abbrechen"),
                  dict(BUTTON_VARIANTS[2], key="dialog.confirm", sample="Absagen")]
DIALOG_TEXT = ("dialog.text", "Alle Eingeladenen erhalten eine Nachricht. Das lässt sich nicht rückgängig machen.")


def draw_dialog(width):
    def draw(pen, x, y):
        pad = T.px("space.6")
        close_size = T.px("space.10")
        assert close_size >= MIN_TARGET
        inner = width - 2 * pad
        title_w = inner - close_size - T.px("space.2")
        _, title_h = pen.text(0, 0, DIALOG_TITLE[1], "heading-h2", "text.primary", width=title_w)
        _, text_h = pen.text(0, 0, DIALOG_TEXT[1], "body-m-regular", "text.secondary", width=inner)
        button_h = button_size("X")[1]
        head_h = max(title_h, close_size)
        h = 2 * pad + head_h + T.px("space.3") + text_h + T.px("space.6") + button_h
        pen.rect(x, y, width, h, fill=T.color("bg.surface"), stroke=T.color("border.default"),
                 radius=T.px("radius.lg"))
        pen.text(x + pad, y + pad, DIALOG_TITLE[1], "heading-h2", "text.primary", width=title_w)
        bx, by = x + width - pad - close_size, y + pad
        pen.rect(bx, by, close_size, close_size, stroke=T.color("border.control"), radius=T.px("radius.md"))
        pen.cross(bx + close_size / 2, by + close_size / 2, 5, T.color("text.secondary"))
        ty = y + pad + head_h + T.px("space.3")
        pen.text(x + pad, ty, DIALOG_TEXT[1], "body-m-regular", "text.secondary", width=inner)
        right = x + width - pad
        for variant in reversed(DIALOG_BUTTONS):
            bw, _ = button_size(variant["sample"])
            right -= bw
            draw_button(variant, "normal")(pen, right, ty + text_h + T.px("space.6"))
            right -= T.px("space.2")
        return width, h
    return draw


def dialog_section(bp):
    full = bp["name"] == "Mobil"
    width = bp["width"] if full else content_width(bp)
    specimens = [Specimen("offen" + (" · volle Breite" if full else ""), draw_dialog(width))]
    notes = [
        ("Mobil: volle Breite des Rahmens, ohne seitlichen Rand." if full else
         "Breite höchstens {size.text-max}, in der Mitte der Seite (hier links gezeichnet)."),
        "Fläche {bg.surface}, Rahmen {border.default}, Ecken {radius.lg}, Innenabstand {space.6},"
        " Schatten {shadow.lg} (im Wireframe nicht gezeichnet).",
        "Titel dialog.title „Termin absagen?“: {typography.style.heading-h2}, {text.primary}; Inhalt dialog.text:"
        " {typography.style.body-m-regular}, {text.secondary}, Abstand {space.3}.",
        "Schließen-Button dialog.close „Schließen“: 40 × 40 px ({space.10}), Rahmen {border.control}, Kreuz"
        " {text.secondary}; Escape schließt ebenfalls.",
        "Aktionen rechtsbündig, Abstand {space.2}: Button sekundär dialog.cancel „Abbrechen“ und Button Gefahr"
        " dialog.confirm „Absagen“.",
        "Fokus beim Öffnen auf das erste Bedienelement, innerhalb des Dialogs gefangen, danach zurück zum"
        " Auslöser; Fokusrahmen {focus.ring}. Die Seite dahinter ist inaktiv (inert).",
        "Es gibt kein Token für die Abdunklung der Seite hinter dem Dialog; sie ist nicht gezeichnet"
        " (siehe Anmerkungen oben).",
    ]
    return Section("Dialog", specimens, notes, full_width=full)


# --- Gesamtbild -------------------------------------------------------

def sections(bp):
    return [button_section(), badge_section(), alert_section(bp), card_section(bp), list_section(bp),
            field_section(bp), dialog_section(bp)]


STORY_STATES = [
    "Normal: bei jeder Komponente gezeichnet.",
    "Laden: Button (laden) und Liste (laden).",
    "Fehler: Alert (Fehler) und Eingabefelder (Fehler mit Fehlermeldung).",
    "Leer: Liste (leer mit Leertext); sonst nicht zutreffend, die Komponenten zeigen selbst keine Daten.",
    "Ohne Berechtigung: nicht zutreffend. Basiskomponenten kennen keine Berechtigung; die Seite entscheidet,"
    " ob sie eine Komponente zeigt.",
]

MISSING_TOKENS = "\n".join([
    "Fehlende Tokens und Varianten (nicht erfunden, Meldung in Ticket 105):",
    "· Info-Alert: bg.info-subtle, border.info und status.info gibt es nicht. Ersatz: {bg.brand-subtle},"
    " {border.brand}, Symbol und Rand mit {text.info}; der Kontrast von {text.info} auf {bg.brand-subtle}"
    " ist nicht geprüft.",
    "· Warnung-Alert: border.warning gibt es nicht. Ersatz: {border.default}.",
    "· Deaktiviert: kein eigenes Token. Ersatz: {bg.muted}, {text.muted}, {border.default}.",
    "· Dialog: kein Token für die Abdunklung der Seite dahinter (overlay.white-20 ist ein Weißschleier);"
    " sie ist nicht gezeichnet.",
    "· Symbole: kein Symbolsatz und kein Größentoken; 24 px und die Zeichen sind Platzhalter.",
    "· Maße ohne Token: Höhe der Bedienelemente 40 px (= {space.10}), Feldbreite 288 px (Hälfte von"
    " {size.text-max}), Höhe des Textbereichs 96 px.",
    "· Laden: es gibt keinen Spinner; Platzhalterbalken in {bg.muted}, Button zeigt nur Text.",
])

CANVAS_NOTES = [
    "Farben, Abstände, Radien und Schriftstile als Token-Namen aus designs/tokens/tokens.json in geschweiften"
    " Klammern. Texte als Fluent-Schlüssel mit Beispieltext (ADR-010). Füllfarben zeigen den hellen Modus;"
    " der dunkle nutzt dieselben Namen.",
    "Alle Komponenten erscheinen in jedem Rahmen. Layoutstufen: Mobil ab 320 px, Tablet ab {breakpoint.tablet},"
    " Desktop ab {breakpoint.desktop}.",
    MISSING_TOKENS,
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
    for bp in BREAKPOINTS:
        draw_breakpoint(wf, bp, x, y, sections(bp))
        x += bp["width"] + ANNOTATION_GAP + ANNOTATION_WIDTH + FRAME_GAP
    wf.write()


if __name__ == "__main__":
    main()
