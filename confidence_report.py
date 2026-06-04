#!/usr/bin/env python3
"""
confidence_report.py <transcript.json> [logprob_thresh=-0.7] [wordscore_thresh=0.4]

Lists the lowest-confidence parts of a WhisperX transcript, ranked, with timestamps —
so meeting notes can flag shaky bits (names, numbers, decisions) as Open Questions.

WhisperX confidence signals:
  - segment 'avg_logprob' : Whisper's own confidence (closer to 0 = better; more negative = worse)
  - word 'score'          : forced-alignment confidence, 0..1 (higher = better)
"""
import sys, json, re

def fmt(t):
    t = max(0, t or 0); m = int(t // 60); s = int(t % 60); h = m // 60
    return f"{h}:{m % 60:02d}:{s:02d}" if h else f"{m}:{s:02d}"

# Function words: low alignment scores on these are noise — we don't care if "is" is uncertain.
STOP = set("a an the and or but so if of to in on at for with by from as is are was were be been "
           "i you he she it we they me him her us them my your his its our their this that these those "
           "do does did will would can could should may might have has had not no yes ok okay yeah uh um "
           "so then than there here what when where who how why which it's i'm don't that's like just".split())

def content_low(words, ws):
    """Low-confidence words that actually matter: proper nouns, numbers, and non-stopword content."""
    out = []
    for w in words:
        sc = w.get("score"); tok = (w.get("word") or "").strip()
        if not isinstance(sc, (int, float)) or not tok:
            continue
        bare = re.sub(r"[^\w']", "", tok)
        low = bare.lower()
        is_num = bool(re.search(r"\d", tok))
        is_proper = bare[:1].isupper()
        is_content = low not in STOP and len(bare) > 2
        # proper nouns / numbers: flag if <0.5; ordinary content words: stricter <0.30
        if (is_proper or is_num) and sc < 0.5:
            out.append((tok, sc, "name/num"))
        elif is_content and sc < 0.30:
            out.append((tok, sc, "word"))
    return out

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: confidence_report.py <transcript.json> [logprob_thresh=-0.6] [wordscore_thresh=0.4]")
    path = sys.argv[1]
    LP = float(sys.argv[2]) if len(sys.argv) > 2 else -0.6
    WS = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4

    d = json.load(open(path, encoding="utf-8"))
    segs = d.get("segments", [])
    flagged = []
    for s in segs:
        lp = s.get("avg_logprob")
        low = content_low(s.get("words") or [], WS)
        lp_bad = isinstance(lp, (int, float)) and lp < LP
        # only surface a segment if Whisper itself was unsure, or it has a shaky NAME/NUMBER
        has_name_num = any(kind == "name/num" for *_, kind in low)
        if not (lp_bad or has_name_num):
            continue
        sev = (LP - lp) * 2 if lp_bad else 0
        sev += sum(0.6 if k == "name/num" else 0.3 for *_, k in low)
        flagged.append((sev, s.get("start", 0), s.get("speaker"), lp, low, (s.get("text") or "").strip()))

    flagged.sort(key=lambda x: -x[0])
    print(f"# Low-confidence report for {path}")
    print(f"# avg_logprob < {LP}  OR  shaky name/number (score<0.5); ordinary words shown if score<0.30")
    print(f"# segments total: {len(segs)} | flagged: {len(flagged)} (showing up to 40)\n")
    for sev, start, spk, lp, low, text in flagged[:40]:
        names = ", ".join(f"'{w}'({sc:.2f})" for w, sc, k in low if k == "name/num") or "-"
        words = ", ".join(f"'{w}'({sc:.2f})" for w, sc, k in low if k == "word") or "-"
        lps = f"{lp:.2f}" if isinstance(lp, (int, float)) else "?"
        print(f"[{fmt(start)}] ({spk or '?'})  logprob={lps}")
        print(f"    names/numbers: {names}")
        print(f"    other low words: {words}")
        print(f"    “{text}”\n")

if __name__ == "__main__":
    main()
