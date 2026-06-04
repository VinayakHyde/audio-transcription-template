# 🎧 Audio → Transcript + AI Notes (Claude Code skill)

Drop in a meeting recording and get back **one self-contained HTML page**: a synced, auto-scrolling transcript on the left and **editable, AI-written notes on the right** — with open questions raised inline and informed by transcription confidence. Fully local; nothing is uploaded.

Built on [WhisperX](https://github.com/m-bain/whisperX) (Whisper `large-v3` + `pyannote` diarization), tuned for Apple Silicon.

---

## ⭐ Just use the skill

Once you've done the one-time **[Setup](#-setup-one-time)** below, you don't run any scripts by hand — you ask **Claude Code** and the bundled **`meeting-notes`** skill does everything (transcribe → write notes → render the page → hand you a URL).

Just say it in plain language:

```
make meeting notes from ~/Downloads/Standup.m4a
```

With options (all optional):

```
make notes from ~/Downloads/Client call.m4a — 2 speakers
make notes from ~/Downloads/Hindi sync.m4a — language hi
make notes from ~/Downloads/Review.m4a — context: I'm the new ops lead building a KPI dashboard; focus on metrics and system gaps
make notes from ~/Downloads/Followup.m4a — context: ~/notes/project-brief.md
```

- **speakers** — exact speaker count for cleaner labels (omit to auto-detect).
- **language** — default `en` (on Hinglish audio this transcribes-as-English, i.e. translates Hindi inline — usually what you want); `hi` for verbatim mixed-script.
- **context** — free text *or a path to a `.md`/`.txt` file*. Steers the whole write-up (reader's role, what to emphasise). If the file carries a **glossary of known people/clients/acronyms**, the skill uses it to **correct shaky transcript spellings and resolve open questions** instead of re-flagging them. Great for follow-up meetings: feed in your running notes and each session resolves the previous one's open items.

**What you get back:** a URL like `http://localhost:8780/Standup.html` (and the same file on disk to double-click). Transcript auto-scrolls + karaoke-highlights as audio plays; scrub or click any line/word to seek; the right pane is your editable notes with clickable `[m:ss]` chips and an Open-Questions trail; low-confidence words are dotted-underlined.

> Heads-up on time: transcription is CPU-only on Apple Silicon, and diarization (speaker labels) is slow — budget ~50 min for a 45-min file, or far less if you skip speaker labels. See [Speed](#speed).

---

## 🛠 Setup (one-time)

### 1. Get the code
```bash
git clone https://github.com/VinayakHyde/audio-transcription-template.git ~/Code/audio-transcription-template
```
> The skill expects the repo at `~/Code/audio-transcription-template`. If you put it elsewhere, edit the `TEMPLATE` path at the top of `skill/SKILL.md`.

### 2. Install the skill into Claude Code
```bash
mkdir -p ~/.claude/skills/meeting-notes
cp ~/Code/audio-transcription-template/skill/SKILL.md ~/.claude/skills/meeting-notes/SKILL.md
```
That's it — Claude Code auto-discovers skills in `~/.claude/skills/`. Start a new Claude Code session and it'll activate when you ask for meeting notes. (Verify by typing `/` — `meeting-notes` should appear.)

### 3. Install ffmpeg
```bash
brew install ffmpeg
```

### 4. Hugging Face token + accept the diarization model
Speaker labels use a **gated** (free) model — accept its terms once:
1. Make a free account at [huggingface.co](https://huggingface.co).
2. Open **https://huggingface.co/pyannote/speaker-diarization-community-1** and click **Agree**. *(This single model replaced the old `speaker-diarization-3.1` + `segmentation-3.0` pair.)*
3. Create a **read** token at **https://huggingface.co/settings/tokens** and export it (add to `~/.zshrc` to persist):
   ```bash
   export HF_TOKEN=hf_your_token_here
   ```
   *(Token only needed for diarization — ask for notes "without speaker labels" to skip it.)*

### 5. First run downloads the models (~3 GB, then cached)
No manual step — the first transcription auto-creates a venv at `~/.whisperx-venv` (`pip install whisperx`) and pulls the models. See the list + links below.

---

## 📦 The models (Hugging Face)

| Model | Purpose | Action |
|-------|---------|--------|
| [**pyannote/speaker-diarization-community-1**](https://huggingface.co/pyannote/speaker-diarization-community-1) | speaker diarization (who spoke when) | **must accept terms** (step 4) |
| [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | transcription (ASR) | auto-downloads |
| torchaudio `WAV2VEC2_ASR_BASE_960H` | word-level alignment (English) | auto-downloads (from pytorch.org) |
| [theainerd/Wav2Vec2-large-xlsr-hindi](https://huggingface.co/theainerd/Wav2Vec2-large-xlsr-hindi) | word alignment (Hindi) | auto-downloads if `language hi` |

WhisperX maps each language to its own alignment model; English uses torchaudio's wav2vec2, other languages pull an equivalent from Hugging Face on demand.

---

## 🔧 Without the skill (manual)

The scripts work standalone too:

```bash
cd ~/Code/audio-transcription-template
./transcribe.sh "/path/to/audio.m4a" 2          # → transcripts/<name>.{json,srt,vtt,txt,tsv,m4a,html}
DIARIZE=0 ./transcribe.sh "/path/to/talk.m4a"   # plain transcript, no speaker labels (much faster)
python3 serve.py 8000 transcripts               # Range-capable server (needed for seeking)
# open http://localhost:8000/<name>.html
```
Env vars: `DIARIZE` (1/0), `WHISPER_LANG` (`en`/`hi`/``), `MODEL` (`large-v3`/`large-v3-turbo`/…), `RENDER` (1/0).
The skill just orchestrates these and writes the notes for you.

> ⚠️ Use the included `serve.py`, **not** `python3 -m http.server` — the built-in server doesn't support HTTP Range, which breaks audio seeking. (Double-clicking the `.html` works too; `file://` is seekable.)

---

## Languages

Whisper decodes **one language per pass** (no simultaneous multi-language).

| `WHISPER_LANG` | Result |
|----------------|--------|
| `en` (default) | English. On **Hinglish/Hindi-English** audio it transcribes-as-English — effectively **translating Hindi inline**, which reads cleanly. |
| `hi` | Hindi — Devanagari for Hindi, Latin for English (verbatim, mixed-script). |
| `""` | Auto-detect (one language for the whole file — flaky on code-mixed audio). |

---

## Speed

Transcription runs on **CPU** (CTranslate2 has no Metal/GPU backend on Apple Silicon). Rough M4 Pro numbers for a **46-min mono file**: transcription ~18 min, **diarization ~33 min** (the slow tail) → ~50 min with speaker labels, ~18 min without (`DIARIZE=0`).

> An MLX/GPU path (`mlx-whisper`) was evaluated and rejected — on accented/code-mixed speech it hallucinated and ran *slower*.

---

## Files

| File | Role |
|------|------|
| `skill/SKILL.md` | the **`meeting-notes`** Claude Code skill (copy to `~/.claude/skills/meeting-notes/`) |
| `transcribe.sh` | audio → transcript + faststart `.m4a` + `.html` |
| `viewer.html` | the player UI (synced transcript + editable notes) |
| `render_page.py` | bakes transcript (+ notes) into a standalone `.html` |
| `confidence_report.py` | ranks low-confidence spans → fuels Open Questions |
| `serve.py` | local web server **with HTTP Range support** (seeking) |
| `transcripts/` | **your outputs — git-ignored** (recordings/transcripts are private) |

---

## Privacy

Everything runs locally; no audio or text leaves your machine. `transcripts/` (recordings, transcripts, and generated pages — which embed the full transcript) is **git-ignored**, so meeting content is never committed.
