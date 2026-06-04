#!/usr/bin/env python3
"""
render_page.py — bake a WhisperX transcript + audio into a single standalone HTML page.

  python3 render_page.py <audio> <transcript.json> <viewer.html> <out.html> [notes.html]

The transcript JSON (and optional notes HTML) are embedded inline -> works from file://.
The audio is referenced relative to the page, so just open the generated .html and it
plays with the synced, auto-scrolling transcript and the editable notes pane.
"""
import sys, os, json, hashlib
from urllib.parse import quote

def main():
    if len(sys.argv) not in (5, 6):
        sys.exit("usage: render_page.py <audio> <transcript.json> <viewer.html> <out.html> [notes.html]")
    audio, jsonp, viewerp, outp = sys.argv[1:5]
    notesp = sys.argv[5] if len(sys.argv) == 6 else None
    name = os.path.splitext(os.path.basename(jsonp))[0]

    with open(viewerp, encoding="utf-8") as f:
        viewer = f.read()
    with open(jsonp, encoding="utf-8") as f:
        transcript = f.read()            # already valid JSON

    notes_html = ""
    if notesp and os.path.isfile(notesp):
        with open(notesp, encoding="utf-8") as f:
            notes_html = f.read()

    # reference audio RELATIVE to the output page (portable; works from file://).
    # When audio sits beside the .html (the normal case) this is just its filename.
    rel = os.path.relpath(os.path.abspath(audio), os.path.dirname(os.path.abspath(outp)))
    audio_url = quote(rel)

    # </ -> <\/ so a stray "</script>" inside text can't close our <script> early.
    # (\/ is a no-op escape in both JSON and JS, so the value stays valid.)
    safe = transcript.replace("</", "<\\/")
    notes_field = json.dumps(notes_html).replace("</", "<\\/")   # embedded as a JS string
    # version stamp: lets the viewer discard stale localStorage edits when notes are regenerated
    notes_ver = hashlib.md5(notes_html.encode("utf-8")).hexdigest()[:12] if notes_html else ""

    embed = ("<script>window.__EMBED={"
             '"audio":' + json.dumps(audio_url) + ','
             '"name":'  + json.dumps(name) + ','
             '"notes":' + notes_field + ','
             '"notesVer":' + json.dumps(notes_ver) + ','
             '"transcript":' + safe +
             "};</script>\n</head>")

    if "</head>" not in viewer:
        sys.exit("viewer.html has no </head> to inject into")
    out = viewer.replace("</head>", embed, 1)

    with open(outp, "w", encoding="utf-8") as f:
        f.write(out)
    print(f">> rendered page: {outp}  ({os.path.getsize(outp)//1024} KB, audio -> {audio_url})")

if __name__ == "__main__":
    main()
