---
name: meeting-notes
description: Transcribe an audio/meeting recording and produce a single self-contained HTML page — a synced, auto-scrolling transcript on the left and AI-written, editable notes on the right. Use when the user gives an audio file (.m4a/.mp3/.wav) and wants notes, meeting minutes, a summary, action items, or a transcript+notes viewer. Drives the local WhisperX pipeline (CPU, Apple Silicon) at ~/Code/audio-transcription-template and writes notes whose Open Questions are informed by transcription confidence scores.
---

# Meeting Notes

Turn a recording into one portable HTML page: synced transcript (left) + your editable notes (right). Notes carry an **Open Questions** section informed by transcription **confidence scores**.

## Location — use these, don't reinvent
`TEMPLATE="$HOME/Code/audio-transcription-template"` holds everything:
`transcribe.sh` · `render_page.py` · `confidence_report.py` · `serve.py` · `viewer.html`.
Requires `HF_TOKEN` in the environment + `ffmpeg`. Diarization model: `pyannote/speaker-diarization-community-1`. Whisper runs on CPU (CTranslate2 has no Metal backend); transcription ≈ 0.4–0.5× realtime and **diarization adds a large tail** (~33 min for a 46-min file) — set expectations and run it in the background.

## Inputs
- **audio** (required): path to the recording.
- **speakers** (optional int): exact speaker count for cleaner labels; omit to auto-detect.
- **language** (optional): default `en`. For Hinglish/Hindi, `hi` often reads better — pass via `WHISPER_LANG`.

## Steps

1. **Set up.** `TEMPLATE="$HOME/Code/audio-transcription-template"`. Verify the audio exists; `ffprobe` its duration and tell the user the rough ETA.

2. **Transcribe** (writes into `$TEMPLATE/transcripts/`, makes a faststart `.m4a` + a no-notes `.html`). Run in the **background** and wait for completion:
   ```bash
   cd "$TEMPLATE" && [WHISPER_LANG=hi] ./transcribe.sh "<audio>" [speakers]
   ```
   Produces `transcripts/<BASE>.{json,srt,vtt,txt,tsv,m4a,html}` where `<BASE>` is the audio filename without extension.

3. **Get the confidence report** (ranked shaky spans with timestamps):
   ```bash
   python3 "$TEMPLATE/confidence_report.py" "$TEMPLATE/transcripts/<BASE>.json"
   ```

4. **Read the transcript** before writing — `transcripts/<BASE>.txt` (speaker-labeled prose) and consult the JSON word `score`s for shaky words. Understand the meeting; do not invent facts.

5. **Write notes** as an HTML fragment to `$TEMPLATE/transcripts/<BASE>.notes.html`. Structure:
   ```html
   <h1>{Meeting title}</h1>
   <h2>Summary</h2><p>2–4 sentences.</p>
   <h2>Key points &amp; decisions</h2><ul><li>… [m:ss]</li></ul>
   <h2>Action items</h2><ul><li><strong>{owner}</strong> — {task} [m:ss]</li></ul>
   <h2>People &amp; roles</h2><ul><li><strong>{name}</strong> — {role}</li></ul>
   <div class="open-q"><h3>Open Questions</h3><ul><li>… [m:ss]</li></ul></div>
   ```
   Rules:
   - **Cite moments as `[m:ss]`** (or `[h:mm:ss]`) liberally — the viewer turns them into clickable seek chips.
   - **Open Questions** come from TWO sources: (a) genuine ambiguities you hit, and (b) **low-confidence spans** from step 3 — especially names, numbers, and decisions. Phrase like: `"[12:34] Bangalore lead's name — transcribed 'Devarshish', low confidence (0.31); confirm spelling."`
   - Optionally wrap an uncertain inline phrase in `<span class="oq">…</span>`.
   - Plain HTML only: `h1–h3, p, ul, li, strong, em, span`. **No markdown, no backticks** (Anki-style rules don't apply here — this is HTML).
   - If diarization clearly mislabeled a turn, say so in a note.

6. **Re-render with notes embedded** (use the faststart `.m4a` copy in `transcripts/`, not the original):
   ```bash
   python3 "$TEMPLATE/render_page.py" \
     "$TEMPLATE/transcripts/<BASE>.m4a" "$TEMPLATE/transcripts/<BASE>.json" \
     "$TEMPLATE/viewer.html" "$TEMPLATE/transcripts/<BASE>.html" \
     "$TEMPLATE/transcripts/<BASE>.notes.html"
   ```

7. **Serve (Range-capable) and give the URL.** Plain `python3 -m http.server` breaks seeking — use `serve.py`:
   ```bash
   python3 "$TEMPLATE/serve.py" 8780 "$TEMPLATE/transcripts"   # background; reuse if already up
   ```
   Give the user: `http://localhost:8780/<BASE>.html` — and mention they can also just **double-click** `transcripts/<BASE>.html` (file:// is seekable too).

## Notes
- The right pane is **editable**; user edits autosave to their browser (localStorage). Your notes are the starting point, not the final word.
- Low-confidence words show a dotted underline in the transcript; that plus the report is what drives Open Questions.
- Speaker labels on mono audio are ~85–90% accurate — infer who's who if you can, and flag uncertainty.
- For a transcript only (no notes), the user can run `transcribe.sh` directly.
