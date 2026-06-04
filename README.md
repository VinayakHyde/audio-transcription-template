# 🎧 Audio Transcription + Synced Notes

Turn any recording into a **single self-contained HTML page**: a synced, auto-scrolling transcript on the left and **editable, AI-written notes on the right**. Fully local and offline after setup — nothing is uploaded.

Built around [WhisperX](https://github.com/m-bain/whisperX) (Whisper `large-v3` + `pyannote` diarization), tuned for Apple Silicon Macs.

![what it does](https://img.shields.io/badge/runs-100%25%20local-success) ![platform](https://img.shields.io/badge/platform-Apple%20Silicon-black)

---

## What you get

- **Word-accurate transcript** with speaker labels (`SPEAKER_00` / `SPEAKER_01` …).
- **Synced player** — the transcript auto-scrolls and karaoke-highlights the current word as audio plays; **scrub** or **click any line/word** to jump.
- **Editable notes pane** — AI-generated meeting notes (Summary · Decisions · Action items · People · **Open Questions**) you can edit in place; edits autosave to your browser.
- **Confidence-aware** — words the model was unsure of get a dotted underline; shaky names/numbers become **Open Questions** in the notes (with clickable `[m:ss]` timestamps).
- **Self-contained output** — one `.html` you can double-click; the audio is bundled (faststart-remuxed so seeking is instant).

---

## Requirements

- macOS on **Apple Silicon** (works elsewhere too; transcription is CPU-only — see [Speed](#speed)).
- [Homebrew](https://brew.sh) · **Python 3.10–3.13** (WhisperX needs `<3.14`) · **ffmpeg**.
- A free **Hugging Face** account + token (for the speaker-diarization model).

---

## Install

### 1. ffmpeg
```bash
brew install ffmpeg
```

### 2. Hugging Face token + model access (for speaker labels)
The diarization model is free but **gated** — accept its terms once:
1. Create a free account at [huggingface.co](https://huggingface.co).
2. Open **[pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)** and click **Agree**. *(This single model replaced the old `speaker-diarization-3.1` + `segmentation-3.0` pair.)*
3. Create a **read** token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), then add it to your shell (persist it in `~/.zshrc`):
   ```bash
   export HF_TOKEN=hf_your_token_here
   ```
   *(Only needed for diarization. Run with `DIARIZE=0` to skip speaker labels and the token.)*

### 3. WhisperX + models
You don't install these by hand — **the first run of `transcribe.sh` bootstraps everything**:
- creates a venv at `~/.whisperx-venv` (Python 3.11) and `pip install whisperx`,
- on first transcription, downloads the models (~**3 GB**, cached afterward): Whisper `large-v3`, `pyannote/speaker-diarization-community-1`, and the `wav2vec2` aligner.

To pre-build the venv manually instead:
```bash
python3.11 -m venv ~/.whisperx-venv
~/.whisperx-venv/bin/pip install whisperx
```

---

## Usage

### Transcribe
```bash
./transcribe.sh "/path/to/Meeting.m4a" 2     # 2 known speakers
./transcribe.sh "/path/to/lecture.m4a"       # auto-detect speaker count
```
Outputs land in **`./transcripts/`** (next to the script): `.json .srt .vtt .txt .tsv`, a faststart `.m4a`, and a ready-to-open `.html` player page.

Options (env vars):
| Var | Default | Effect |
|-----|---------|--------|
| `DIARIZE` | `1` | `0` = plain transcript, no speaker labels (much faster — skips the diarization tail) |
| `WHISPER_LANG` | `en` | language code; `""` to auto-detect. See [Languages](#languages) |
| `MODEL` | `large-v3` | `large-v3-turbo` (faster), `medium`, `small` |
| `RENDER` | `1` | `0` = skip building the `.html` page |

### View / play
Two ways:
- **Double-click** `transcripts/<name>.html` — it's self-contained and seekable (`file://`).
- **Serve it** (needed only if you prefer a URL) — use the included Range-capable server; the built-in `python3 -m http.server` does **not** support range requests and will break seeking:
  ```bash
  python3 serve.py 8000 transcripts
  # open http://localhost:8000/<name>.html
  ```

Player shortcuts: `Space` play/pause · `←/→` ±5s · `j/l` ±10s. Rename `SPEAKER_xx` → real names in the header (saved locally). Search box + 0.75–2× speed.

### AI notes (the `meeting-notes` skill)
This repo ships a **Claude Code skill** that runs the whole pipeline *and* writes the notes. Install it:
```bash
mkdir -p ~/.claude/skills/meeting-notes
cp skill/SKILL.md ~/.claude/skills/meeting-notes/
```
Then in Claude Code: *"make meeting notes from ~/Downloads/Meeting.m4a"*. It transcribes, reads the transcript + confidence report, writes structured notes (Open Questions informed by low-confidence spans), renders the page, and gives you a URL. The notes pane is your starting point — edit freely.

To (re)generate notes for an already-transcribed file by hand:
```bash
python3 confidence_report.py "transcripts/<name>.json"      # see the shaky spans
# ...write transcripts/<name>.notes.html (plain HTML: h1-h3, p, ul/li; cite moments as [m:ss];
#    wrap Open Questions in <div class="open-q">…</div>)...
python3 render_page.py "transcripts/<name>.m4a" "transcripts/<name>.json" \
        viewer.html "transcripts/<name>.html" "transcripts/<name>.notes.html"
```

---

## Languages

Whisper decodes **one language per pass** (no simultaneous multi-language).

| `WHISPER_LANG` | Result |
|----------------|--------|
| `en` (default) | English. On **Hinglish/Hindi-English** audio this transcribes-as-English — it effectively **translates Hindi inline into English**, which reads cleanly. |
| `hi` | Hindi — Devanagari for Hindi, Latin for English (verbatim, mixed-script). |
| `""` | Auto-detect (picks one language for the whole file — flaky on code-mixed audio). |

For an explicit English translation of any-language audio, add `--task translate` to the `whisperx` args in `transcribe.sh`.

---

## Speed

Whisper runs on **CPU** on Apple Silicon — CTranslate2 has no Metal/GPU backend. Rough numbers on an M4 Pro for a **46-min mono file**: transcription ~18 min, **diarization ~33 min** (the slow tail). So budget ~50 min with speaker labels, ~18 min without (`DIARIZE=0`).

> An MLX/GPU path (`mlx-whisper`) was evaluated and rejected — on accented/code-mixed speech it hallucinated and ran *slower*. CPU WhisperX gave clean output.

---

## Files

| File | Role |
|------|------|
| `transcribe.sh` | audio → transcript (`.json/.srt/.vtt/.txt/.tsv`) + faststart `.m4a` + `.html` |
| `viewer.html` | the player UI (synced transcript + editable notes); works via drag-drop, `?audio=&transcript=` params, or an embedded payload |
| `render_page.py` | bakes transcript (+ optional notes) into a standalone `.html` |
| `confidence_report.py` | ranks low-confidence spans → fuels Open Questions |
| `serve.py` | local web server **with HTTP Range support** (seeking) |
| `skill/SKILL.md` | the `meeting-notes` Claude Code skill |
| `transcripts/` | **your outputs — git-ignored** (recordings/transcripts are private) |

---

## Privacy

Everything runs locally; no audio or text leaves your machine. The `transcripts/` folder (recordings, transcripts, generated pages — which embed the full transcript) is **git-ignored** so private meeting content is never committed.
