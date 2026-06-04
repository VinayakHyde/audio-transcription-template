#!/usr/bin/env bash
#
# transcribe.sh — local audio → speaker-labeled transcript + a standalone player page.
# Whisper large-v3 (transcription) + pyannote diarization, via WhisperX. Tuned for Apple Silicon.
# Everything is written into THIS folder's ./transcripts (next to the script), not your cwd.
#
# USAGE:
#   ./transcribe.sh /path/to/audio.m4a [num_speakers]
#
#   ./transcribe.sh ~/Downloads/"Meeting with Amrit.m4a" 2   # 2 known speakers
#   ./transcribe.sh ~/Downloads/lecture.m4a                  # auto-detect speaker count
#   DIARIZE=0 ./transcribe.sh ~/Downloads/talk.m4a           # plain transcript, no speakers (faster)
#   RENDER=0  ./transcribe.sh ...                            # skip building the .html page
#
# ONE-TIME SETUP:
#   1. ffmpeg:    brew install ffmpeg
#   2. Accept the diarization model terms (2026 — just this one model):
#        https://huggingface.co/pyannote/speaker-diarization-community-1  -> "Agree"
#   3. Create a READ token at https://huggingface.co/settings/tokens, then add to your shell:
#        export HF_TOKEN=hf_your_token_here          # (put in ~/.zshrc to persist)
#
set -euo pipefail

# resolve this script's own directory, so output is folder-relative no matter the cwd
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

AUDIO="${1:?Usage: ./transcribe.sh /path/to/audio.(m4a|mp3|wav) [num_speakers]}"
SPEAKERS="${2:-}"

# ----- settings -----
MODEL="${MODEL:-large-v3}"          # large-v3 (best) | large-v3-turbo (faster) | medium | small
LANG_CODE="${WHISPER_LANG:-en}"     # "" to auto-detect language (don't use $LANG — that's the OS locale)
DIARIZE="${DIARIZE:-1}"             # 1 = speaker labels (default), 0 = plain transcript
RENDER="${RENDER:-1}"               # 1 = also build the standalone .html player page
VENV="${VENV:-$HOME/.whisperx-venv}"
OUTDIR="${OUTDIR:-$SCRIPT_DIR/transcripts}"   # <-- lands inside the template folder
VIEWER="$SCRIPT_DIR/viewer.html"

# ----- one-time environment bootstrap (skipped once the venv exists) -----
if [ ! -d "$VENV" ]; then
  echo ">> First run: creating Python env at $VENV (WhisperX needs Python >=3.10,<3.14)"
  PYBIN="$(command -v python3.11 || command -v python3.12 || command -v python3.13 || command -v python3.10 || command -v python3)"
  echo ">> interpreter: $PYBIN ($("$PYBIN" --version 2>&1))"
  "$PYBIN" -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip
  "$VENV/bin/pip" install whisperx
fi

mkdir -p "$OUTDIR"

# ----- assemble args -----
ARGS=( "$AUDIO" --model "$MODEL" --device cpu --compute_type int8
       --output_dir "$OUTDIR" --output_format all )
[ -n "$LANG_CODE" ] && ARGS+=( --language "$LANG_CODE" )

if [ "$DIARIZE" = "1" ]; then
  : "${HF_TOKEN:?Diarization needs a token: export HF_TOKEN=hf_xxxx (or run with DIARIZE=0)}"
  ARGS+=( --diarize --hf_token "$HF_TOKEN" )
  [ -n "$SPEAKERS" ] && ARGS+=( --min_speakers "$SPEAKERS" --max_speakers "$SPEAKERS" )
  echo ">> diarization: ON (model pyannote/speaker-diarization-community-1)"
else
  echo ">> diarization: OFF (plain transcript — much faster)"
fi

echo ">> transcribing: $AUDIO"
echo ">> model: $MODEL   device: cpu (CTranslate2 has no Metal backend on Apple Silicon)"
echo ">> output: $OUTDIR"
START=$(date +%s)

"$VENV/bin/whisperx" "${ARGS[@]}"

ELAPSED=$(( $(date +%s) - START ))
echo ">> transcription done in $((ELAPSED/60))m $((ELAPSED%60))s."

# ----- build the standalone, self-contained HTML player page -----
BASE="$(basename "$AUDIO")"; BASE="${BASE%.*}"
JSON_OUT="$OUTDIR/$BASE.json"
if [ "$RENDER" = "1" ] && [ -f "$JSON_OUT" ]; then
  # Put a browser-SEEKABLE copy of the audio in the folder (moov atom moved to the front).
  # Without this, m4a recordings won't scrub or click-to-seek until fully buffered.
  EXT="$(printf '%s' "${AUDIO##*.}" | tr '[:upper:]' '[:lower:]')"
  case "$EXT" in
    m4a|mp4|mov|aac|m4b)
      AUDIO_LOCAL="$OUTDIR/$BASE.m4a"
      ffmpeg -y -i "$AUDIO" -c copy -movflags +faststart "$AUDIO_LOCAL" >/dev/null 2>&1 \
        || cp "$AUDIO" "$AUDIO_LOCAL" ;;
    *) AUDIO_LOCAL="$OUTDIR/$BASE.$EXT"; cp "$AUDIO" "$AUDIO_LOCAL" ;;
  esac
  python3 "$SCRIPT_DIR/render_page.py" "$AUDIO_LOCAL" "$JSON_OUT" "$VIEWER" "$OUTDIR/$BASE.html"
  echo ">> Open it:  open \"$OUTDIR/$BASE.html\""
fi

echo ">> outputs in: $OUTDIR  (.txt .srt .vtt .json .tsv$([ "$RENDER" = "1" ] && echo " .html"))"
[ "$DIARIZE" = "1" ] && echo ">> Speakers are SPEAKER_00 / SPEAKER_01 ... — rename them right inside the page."
