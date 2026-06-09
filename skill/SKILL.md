---
name: meeting-notes
description: Transcribe an audio/meeting recording and produce a single self-contained HTML page — a synced, auto-scrolling transcript on the left and AI-written, editable notes on the right. Use when the user gives an audio file (.m4a/.mp3/.wav) and wants notes, meeting minutes, a summary, action items, or a transcript+notes viewer. Drives the local WhisperX pipeline (CPU, Apple Silicon) at ~/Code/audio-transcription-template and writes detailed notes whose open questions are placed inline and informed by transcription confidence scores.
---

# Meeting Notes

Turn a recording into one portable HTML page: synced transcript (left) + your editable notes (right), with **open questions raised inline at the exact point each note is made**, informed by transcription **confidence scores**.

## Location — use these, don't reinvent
`TEMPLATE="$HOME/Code/audio-transcription-template"` holds everything:
`transcribe.sh` · `render_page.py` · `confidence_report.py` · `serve.py` · `viewer.html`.
Requires `HF_TOKEN` in the environment + `ffmpeg`. Diarization model: `pyannote/speaker-diarization-community-1`. Whisper runs on CPU (CTranslate2 has no Metal backend); transcription ≈ 0.4–0.5× realtime and **diarization adds a large tail** (~33 min for a 46-min file) — set expectations and run it in the background.

## Inputs
- **audio** (required): path to the recording.
- **speakers** (optional int): exact speaker count for cleaner labels; omit to auto-detect.
- **language** (optional): default `en`. Note: `en` on Hinglish audio transcribes-as-English (translates Hindi inline) — usually desired. `hi` for verbatim mixed-script.
- **context** (optional): who the notes are for and what to emphasise — reader's role/goals, the angle, themes to prioritise, terminology/format. May be given **inline as free text OR as a path to a `.md`/`.txt` file** — if it looks like a file path, `Read` it and use its full contents as the context. A file is ideal for a standing brief the user reuses across meetings: their role, the project, an **org glossary / known people & clients / acronyms / naming conventions**. Steers the entire write-up (see step 5). Example inline: *"I'm the new ops lead building a KPI dashboard — focus on metrics and system gaps, frame action items for me."*

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

4. **Read the whole transcript** before writing — `transcripts/<BASE>.txt` (speaker-labeled prose). Genuinely understand the meeting; never invent facts.

5. **Write notes** to `$TEMPLATE/transcripts/<BASE>.notes.html` — **detailed, in-depth, and structured. NOT a terse summary.** Someone who missed the meeting should be able to reconstruct it from your notes: capture how things work, the specifics, names, numbers, processes, decisions, and the reasoning — not just headlines.

   **If `context` was provided, let it steer everything** — the reader's perspective and goals decide which themes to expand vs compress, what counts as an action item or open question, the section ordering, the title, and the terminology. Examples: *"I'm the new ops lead building a KPI dashboard"* → lead with metrics/systems, frame action items for that reader, surface data gaps as open questions; *"for the CEO, keep it strategic"* → emphasise decisions, risks, and money, trim operational minutiae; *"prep for a follow-up negotiation"* → pull out commitments, numbers, and leverage points. Without context, write balanced, general-purpose meeting notes. Either way, keep the inline-open-question discipline below.

   If `context` is a file path, `Read` it first. When the context supplies a **glossary or known entities** (people, clients, the company name, acronyms), use them to **correct shaky transcript spellings and resolve open questions** — e.g. a name the audio rendered as "Devarshish" becomes a confirmed fact (not an open question) if the brief lists the real spelling; expand acronyms like "OI"/"CPC" if the brief defines them.

   **A glossary term OVERRIDES the transcript — always — even when the audio repeats the wrong form dozens of times.** The transcript is raw ASR; the glossary is ground truth. If the glossary says the term is "KAM" but the audio says "CAM" throughout, write **KAM** everywhere in the notes (likewise Aanchal-not-Anshul, the real company name, etc.). Before finishing, do a **find-and-replace pass over the notes** for every glossary-corrected term to catch any that slipped through in the transcript's spelling. Do NOT flag a glossary-confirmed term as an open question.

   **Organize into themed `<h2>` sections** (with `<h3>` sub-sections where it helps), each unpacking real content with detailed `<ul>` bullets or `<ol>` step lists. Adapt the sections to the meeting; a typical spine:
   ```html
   <h1>{Title}</h1><p>1–2 sentence context (who/what).</p>
   <h2>1. {theme}</h2><ul><li>detailed point … [m:ss]</li> …</ul>
   <h2>2. {process / lifecycle}</h2><ol><li>step … [m:ss]</li> …</ol>
   <h2>People &amp; roles</h2><ul>…</ul>
   <h2>Decisions</h2> … <h2>Action items</h2><ul><li><strong>{owner}</strong> — {task} [m:ss]</li></ul>
   ```

   **Open questions go INLINE — at the exact point the note is made, not pooled at the bottom.** Immediately after the bullet/point they relate to, drop:
   ```html
   <div class="oq-inline">…the question, the [m:ss], and exactly what's uncertain…</div>
   ```
   Raise one whenever: (a) you hit a genuine ambiguity, or (b) the confidence report (step 3) flags a low-confidence **name / number / decision** at that point. Prefer wrapping the uncertain phrase itself in `<span class="oq">…</span>` inside the note, then explain in the adjacent `.oq-inline`. Example:
   ```html
   <li>Mobilization head is based in Bengaluru, titled CBO [0:55].
     <div class="oq-inline">Name transcribed as <span class="oq">"Devarshish / Deeparshish"</span> — speakers disagreed, low confidence; confirm spelling.</div>
   </li>
   ```

   Rules:
   - **Cite moments as `[m:ss]`** (or `[h:mm:ss]`) liberally — the viewer turns them into clickable seek chips.
   - Be thorough and specific; use the actual content. If diarization clearly mislabeled a turn, note it inline.
   - Plain HTML only: `h1–h3, p, ul, ol, li, strong, em, span.oq, div.oq-inline`. **No markdown, no backticks.**

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
- The right pane is **editable**; user edits autosave to their browser (localStorage). Your notes are the starting point.
- Low-confidence words show a dotted underline in the transcript; that plus the report is what drives the inline open questions.
- Speaker labels on mono audio are ~85–90% accurate — infer who's who if you can, and flag uncertainty inline.
- For a transcript only (no notes), the user can run `transcribe.sh` directly.
