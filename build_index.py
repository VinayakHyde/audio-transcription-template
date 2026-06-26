#!/usr/bin/env python3
"""Generate transcripts/index.html — every meeting grouped by date, linking to its page.
Usage: python3 build_index.py [transcripts_dir]   (default: ./transcripts next to this script)
Re-run any time after adding meetings.
"""
import os, re, sys, html, datetime
from urllib.parse import quote

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcripts")

def title_of(notes_path, fallback):
    try:
        t = open(notes_path, encoding="utf-8", errors="ignore").read()
        m = re.search(r"<h1>(.*?)</h1>", t, re.S)
        if m:
            return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    except Exception:
        pass
    return fallback

dates = sorted([d for d in os.listdir(ROOT)
                if os.path.isdir(os.path.join(ROOT, d)) and re.match(r"\d{4}-\d{2}-\d{2}$", d)],
               reverse=True)
rows = []
total = 0
for date in dates:
    dp = os.path.join(ROOT, date)
    mtgs = sorted([m for m in os.listdir(dp) if os.path.isdir(os.path.join(dp, m))])
    if not mtgs:
        continue
    items = []
    for m in mtgs:
        page = f"{m}/{m}.html"
        if not os.path.exists(os.path.join(dp, m, f"{m}.html")):
            # fall back to any .html in the folder
            htmls = [f for f in os.listdir(os.path.join(dp, m)) if f.endswith(".html") and not f.endswith(".notes.html")]
            if not htmls:
                continue
            page = f"{m}/{htmls[0]}"
        title = title_of(os.path.join(dp, m, f"{m}.notes.html"), m)
        href = quote(f"{date}/{page}")
        items.append(f'    <li><a href="{href}">{html.escape(m)}</a><span class="t">{html.escape(title)}</span></li>')
        total += 1
    try:
        pretty = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%a %d %b %Y")
    except Exception:
        pretty = date
    rows.append(f'  <section><h2>{pretty} <span class="n">{len(items)}</span></h2>\n  <ul>\n' + "\n".join(items) + "\n  </ul></section>")

doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meeting notes — index ({total})</title>
<style>
:root{{color-scheme:dark light}}
*{{box-sizing:border-box}}
body{{font:16px/1.5 system-ui,-apple-system,sans-serif;max-width:880px;margin:0 auto;padding:2rem 1.2rem;
 background:#0f1115;color:#e6e6e6}}
h1{{font-size:1.5rem;margin:0 0 .2rem}}
.sub{{color:#8b93a1;margin:0 0 2rem;font-size:.9rem}}
section{{margin:0 0 1.6rem}}
h2{{font-size:1rem;color:#9ecbff;border-bottom:1px solid #232733;padding-bottom:.3rem;margin:0 0 .5rem;
 display:flex;align-items:baseline;gap:.5rem}}
h2 .n{{font-size:.75rem;color:#6b7280;font-weight:400}}
ul{{list-style:none;margin:0;padding:0}}
li{{padding:.4rem .5rem;border-radius:6px}}
li:hover{{background:#171a21}}
a{{color:#e6e6e6;text-decoration:none;font-weight:600}}
a:hover{{color:#9ecbff;text-decoration:underline}}
.t{{display:block;color:#8b93a1;font-size:.82rem;font-weight:400;margin-top:.1rem}}
</style></head><body>
<h1>Meeting notes</h1>
<p class="sub">{total} meetings · transcript + AI notes · newest first</p>
{chr(10).join(rows)}
</body></html>"""

out = os.path.join(ROOT, "index.html")
open(out, "w", encoding="utf-8").write(doc)
print(f"wrote {out} — {total} meetings across {len(rows)} dates")
