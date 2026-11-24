# designs/

Entwürfe und Design-Grundlagen für Chronos. Nicht Teil von `docs/`: nichts hier ist freigegeben, solange kein Vorschlag nach `docs/` angenommen ist.

| Pfad | Inhalt |
|---|---|
| `tokens/tokens.json` | Design-Tokens im W3C-DTCG-Format: Farben (Primitives, Hell/Dunkel), Abstände, Radien, Typografie, Schatten, Verläufe. Von Hand gepflegte Quelle der Werte. |
| `wireframes/` | Wireframes je Story als Excalidraw (siehe unten) |

Es liegt bewusst kein Figma-Export im Repo, nur die extrahierten Werte.

## Wireframes
- Werkzeug: Excalidraw. Pro Story **eine** Datei `wireframes/S<Ticketnummer>-<kurzname>.excalidraw` mit drei beschrifteten Rahmen **Mobil 320 px**, **Tablet 768 px** und **Desktop 1280 px**; daneben der SVG-Export gleichen Namens (für Review im PR ohne Editor).
- Jeder Rahmen zeigt alle Zustände der Story (normal, leer, laden, Fehler, ohne Berechtigung).
- Farben und Abstände nur über Token-Namen (`bg.surface`, `text.brand`, `space.4`), nie über Hex-Werte.
- Das Ticket verlinkt den Pfad im Abschnitt „Hinweise“.
