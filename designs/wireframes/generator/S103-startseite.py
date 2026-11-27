"""Wireframe der Startseite zu Ticket 103 (Task 114).

Dieses Skript ist die Quelle von S103-startseite.excalidraw und S103-startseite.svg.
Wird die Excalidraw-Datei im Editor von Hand bearbeitet, dieses Skript danach nicht mehr ausführen:
Es überschreibt beide Dateien und die Handarbeit geht verloren.

Aufruf: python3 -I designs/wireframes/generator/S103-startseite.py
"""
import os
import sys

# -I nimmt das Skriptverzeichnis nicht in sys.path auf.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wirelib import ANNOTATION_TEXT, CHROME_STROKE, CHROME_TEXT, Tokens, Wireframe, wrap  # noqa: E402

T = Tokens()

TEXT_MAX = "size.text-max"
MOBILE_MIN_WIDTH = 320

BREAKPOINTS = [
    dict(name="Mobil", width=MOBILE_MIN_WIDTH, range="Mobil bis unter {breakpoint.tablet}",
         top="space.8", side="space.4"),
    dict(name="Tablet", width=T.px("breakpoint.tablet"), range="Tablet ab {breakpoint.tablet}",
         top="space.16", side="space.8"),
    dict(name="Desktop", width=T.px("breakpoint.desktop"), range="Desktop ab {breakpoint.desktop}",
         top="space.16", side="space.12"),
]

TITLE = dict(kind="text", key="start.title", sample="Chronos", style="heading-h1", color="text.primary")
LOADING_TITLE = dict(kind="text", key="app.name", sample="Chronos", style="heading-h1", color="text.primary")
NOT_FOUND_TITLE = dict(kind="text", key="error.not-found.title", sample="Seite nicht gefunden",
                       style="heading-h1", color="text.primary")


def gap(space):
    return dict(kind="gap", space=space)


STATES = [
    dict(caption="Zustand: Normal", content=[
        TITLE, gap("space.2"),
        dict(kind="text", key="start.intro", sample="Termine im Leitungsteam planen und Rückmeldungen einholen.",
             style="body-m-regular", color="text.secondary"),
    ], notes=[]),
    dict(caption="Zustand: Laden", content=[
        LOADING_TITLE, gap("space.2"),
        dict(kind="text", key="app.loading", sample="Wird geladen …", style="body-s-regular", color="text.muted",
             extra="role=status"),
    ], notes=[
        "Hülle aus index.html, sichtbar bis das Skript geladen ist. Kein Spinner, keine Skeleton-Komponente.",
        "Texte stehen statisch in index.html, nicht über t(). Wert aus dem Katalog übernehmen (V-3, Hinweis an Ticket 103).",
    ]),
    dict(caption="Zustand: Fehler (Adresse unbekannt)", content=[
        NOT_FOUND_TITLE, gap("space.2"),
        dict(kind="text", key="error.not-found.text", sample="Diese Adresse gibt es in Chronos nicht.",
             style="body-m-regular", color="text.secondary"),
        gap("space.6"),
        dict(kind="link", key="error.not-found.home", sample="Zur Startseite", style="body-m-semibold",
             color="text.brand", extra="Ziel /, unterstrichen, Fokus {focus.ring}"),
    ], notes=[
        "Gilt für jede unbekannte Adresse; die Seite hat ein eigenes h1.",
        "Der Link ist der Seitenwechsel, den Ticket 116 testet.",
    ]),
]

NOT_APPLICABLE = [
    "Leer: nicht zutreffend. Die Startseite zeigt keine Daten.",
    "Ohne Berechtigung: nicht zutreffend. Es gibt keine Anmeldung.",
]

CANVAS_NOTES = [
    "Farben, Abstände und Schriftstile als Token-Namen aus designs/tokens/tokens.json in geschweiften Klammern."
    " Texte als Fluent-Schlüssel mit Beispieltext (ADR-010). Füllfarben zeigen den hellen Modus;"
    " der dunkle nutzt dieselben Namen.",
    "Layoutstufen: Mobil ab 320 px, Tablet ab {breakpoint.tablet}, Desktop ab {breakpoint.desktop}."
    " Die Textspalte ist höchstens {size.text-max} breit (gestrichelte Linie).",
]

SCREEN_HEIGHT = 400
CAPTION_HEIGHT = 32
ROW_GAP = 40
ANNOTATION_GAP = 24
ANNOTATION_WIDTH = 440
FRAME_GAP = 48
FRAME_PADDING = 16
NOTE_SIZE = 14
NOTE_LINE = 20
NOTE_PADDING = 8
CANVAS_WIDTH = sum(bp["width"] for bp in BREAKPOINTS) + 3 * (ANNOTATION_GAP + ANNOTATION_WIDTH) + 2 * FRAME_GAP


def describe(item):
    role = "h1 " if item["style"] == "heading-h1" else ("Link " if item["kind"] == "link" else "")
    text = "%s%s „%s“: {typography.style.%s}, {%s}" % (role, item["key"], item["sample"], item["style"],
                                                         item["color"])
    if item.get("extra"):
        text += "; " + item["extra"]
    return text


def draw_content(wf, frame, x, y, width, content):
    """Zeichnet den Inhalt eines Zustands und gibt die Anmerkungen dazu zurück."""
    notes = []
    for item in content:
        if item["kind"] == "gap":
            y += T.px(item["space"])
            notes.append("Abstand {%s}" % item["space"])
            continue
        style = T.type_style(item["style"])
        w, h = wf.text(x, y, item["sample"], style["size"], style["line"], T.color(item["color"]),
                       width=width, bold=style["bold"], frame=frame)
        if item["kind"] == "link":
            wf.line(x, y + h - 2, x + w, y + h - 2, T.color(item["color"]), frame=frame)
        notes.append(describe(item))
        y += h
    return notes


def draw_breakpoint(wf, bp, x, y):
    side, top, width = T.px(bp["side"]), T.px(bp["top"]), bp["width"]
    text_max = T.px(TEXT_MAX)
    text_width = min(width - 2 * side, text_max)
    na_text = "\n".join(NOT_APPLICABLE)
    na_height = len(wrap(na_text, width - 2 * FRAME_PADDING, NOTE_SIZE)) * NOTE_LINE + 2 * NOTE_PADDING
    frame_height = len(STATES) * (CAPTION_HEIGHT + SCREEN_HEIGHT + ROW_GAP) + na_height + 2 * FRAME_PADDING
    frame = wf.frame("%s %d px" % (bp["name"], width), x, y, width, frame_height)
    annotation_x = x + width + ANNOTATION_GAP

    row_y = y + FRAME_PADDING
    for state in STATES:
        wf.text(x + FRAME_PADDING, row_y, state["caption"], 16, CAPTION_HEIGHT, CHROME_TEXT, frame=frame)
        screen_y = row_y + CAPTION_HEIGHT
        wf.rect(x, screen_y, width, SCREEN_HEIGHT, fill=T.color("bg.page"), stroke=CHROME_STROKE, frame=frame)
        notes = ["%s: Seite {bg.page}; Rand oben {%s}, seitlich {%s}" % (bp["range"], bp["top"], bp["side"])]
        notes += draw_content(wf, frame, x + side, screen_y + top, text_width, state["content"])
        if width - 2 * side > text_max:
            guide_x = x + side + text_max
            wf.line(guide_x, screen_y + 8, guide_x, screen_y + SCREEN_HEIGHT - 8, CHROME_STROKE, dashed=True,
                    frame=frame)
            notes.append("Gestrichelt: maximale Textbreite {%s}" % TEXT_MAX)
        notes += state["notes"]
        wf.text(annotation_x, screen_y, "\n".join("· " + n for n in notes), NOTE_SIZE, NOTE_LINE, ANNOTATION_TEXT,
                width=ANNOTATION_WIDTH)
        row_y = screen_y + SCREEN_HEIGHT + ROW_GAP
    wf.rect(x + FRAME_PADDING / 2, row_y, width - FRAME_PADDING, na_height, dashed=True, frame=frame)
    wf.text(x + FRAME_PADDING, row_y + NOTE_PADDING, na_text, NOTE_SIZE, NOTE_LINE, CHROME_TEXT,
            width=width - 2 * FRAME_PADDING, frame=frame)


def main():
    wf = Wireframe("S103-startseite", "chronos-v3/designs/wireframes/generator/S103-startseite.py")
    wf.text(0, 0, "S103 Startseite: Wireframe zu Ticket 103 (Task 114)", 28, 36, CHROME_TEXT)
    y = 44
    for note in CANVAS_NOTES:
        _, h = wf.text(0, y, note, 15, 22, ANNOTATION_TEXT, width=CANVAS_WIDTH)
        y += h + 6
    x, y = 0, y + 56
    for bp in BREAKPOINTS:
        draw_breakpoint(wf, bp, x, y)
        x += bp["width"] + ANNOTATION_GAP + ANNOTATION_WIDTH + FRAME_GAP
    wf.write()


if __name__ == "__main__":
    main()
