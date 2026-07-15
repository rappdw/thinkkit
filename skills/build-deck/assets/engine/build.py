#!/usr/bin/env python3
"""Compose the two self-contained presentation windows from src/ + fragments/ + manifest.json.

Run from a deck project root (the directory that holds manifest.json, src/, fragments/).

Usage:
  python3 build.py                 -> writes slides.html and presenter.html
  python3 build.py --preview s2    -> also writes preview-s2.html (single-slide harness)
  python3 build.py --sync-manifest -> rewrite manifest step-counts from fragments (fragments win)

Everything is inlined; outputs make zero network requests and run from file://.

Manifest keys read here:
  title            (str)  deck title -> audience window <title>
  presenterTitle   (str, optional) presenter window <title>; default "<title> — PRESENTER (do not share)"
  order            (list) slide ids in order
  slides           (obj)  { id: { steps, budget, title } }
  appendix         (str|null, optional) appendix fragment id (shown on the C key)
"""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).parent
SRC, FRAG = ROOT / "src", ROOT / "fragments"

def read(p): return Path(p).read_text(encoding="utf-8")

def build(manifest_path=ROOT / "manifest.json"):
    m = json.loads(read(manifest_path))
    title = m.get("title", "Presentation")
    presenter_title = m.get("presenterTitle", f"{title} — PRESENTER (do not share)")
    tokens, slides_css, presenter_css = read(SRC/"tokens.css"), read(SRC/"slides.css"), read(SRC/"presenter.css")
    state_js, runtime_js = read(SRC/"state.js"), read(SRC/"runtime.js")
    manifest_js = "window.DECK_MANIFEST = " + json.dumps(m) + ";"

    missing = []
    frags, notes = [], []
    for sid in m["order"]:
        f, n = FRAG/f"{sid}.html", FRAG/f"{sid}-notes.html"
        if f.exists(): frags.append(read(f))
        else: missing.append(str(f))
        if n.exists(): notes.append(read(n))
        else: missing.append(str(n))
    apx_html = ""
    if m.get("appendix"):
        ap = FRAG/f"{m['appendix']}.html"
        if ap.exists(): apx_html = read(ap)
        else: missing.append(str(ap))
    if missing:
        sys.exit("MISSING FRAGMENTS:\n  " + "\n  ".join(missing))
    ref = FRAG / "presenter-ref.html"
    presenter_ref = read(ref) if ref.exists() else "(no presenter-ref fragment)"

    slides_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{tokens}
{slides_css}
</style></head>
<body>
<div class="stage"><div class="frame">
{''.join(frags)}
<div id="slide-footer"><span id="slide-num"></span></div>
<div id="apx-overlay">{apx_html}</div>
<div id="blank-overlay"></div>
</div></div>
<script>{manifest_js} window.DECK_ROLE='audience';</script>
<script>{state_js}</script>
<script>{runtime_js}</script>
</body></html>"""

    keys_legend = ("<kbd>SPACE</kbd>/<kbd>→</kbd> advance · <kbd>←</kbd> back · "
                   "<kbd>PgUp</kbd>/<kbd>PgDn</kbd> whole slide · <kbd>Home</kbd>/<kbd>End</kbd> · "
                   "<kbd>B</kbd> blank audience · <kbd>C</kbd> appendix · <kbd>Q</kbd> Q&amp;A card · "
                   "<kbd>T</kbd> clock start/stop · keys work in either window")

    presenter_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{presenter_title}</title>
<style>
{tokens}
{presenter_css}
</style></head>
<body>
<div class="pc-header">
  <span class="brand">PRESENTER — DO NOT SHARE</span>
  <span id="pc-clock">00:00</span>
  <span id="pc-pace" class="pace"></span>
  <span id="pc-flags"></span>
  <button id="pc-open-audience">Open audience window</button>
</div>
<div class="pc-current">
  <span id="pc-slide-title"></span>
  <span id="pc-steps"></span>
  <span id="pc-budget"></span>
  <span id="pc-next"></span>
</div>
{''.join(notes)}
<details class="pc-ref"><summary>Q&amp;A prep + overrun plan (presenter-only)</summary>
<div class="ref-body">{presenter_ref}</div>
</details>
<div class="pc-keys">{keys_legend}</div>
<script>{manifest_js} window.DECK_ROLE='presenter';</script>
<script>{state_js}</script>
<script>{runtime_js}</script>
</body></html>"""

    (ROOT/"slides.html").write_text(slides_html, encoding="utf-8")
    (ROOT/"presenter.html").write_text(presenter_html, encoding="utf-8")
    print(f"built: slides.html ({len(slides_html):,} bytes), presenter.html ({len(presenter_html):,} bytes)")

    # external-reference audit: fail the build on any network fetch
    leaks = []
    for name, doc in (("slides.html", slides_html), ("presenter.html", presenter_html)):
        for pat in (r'src="https?://', r'href="https?://', r'url\(\s*[\'"]?https?://', r'@import', r'fetch\('):
            if re.search(pat, doc): leaks.append(f"{name}: {pat}")
    if leaks:
        sys.exit("EXTERNAL REFERENCES FOUND:\n  " + "\n  ".join(leaks))
    print("audit: zero external references in both outputs")

def preview(sid):
    m = json.loads(read(ROOT/"manifest.json"))
    if sid not in m["slides"]:
        sys.exit(f"unknown slide id: {sid}")
    frag = read(FRAG/f"{sid}.html")
    entry = dict(m["slides"][sid])
    ds = re.search(r'data-steps="(\d+)"', frag)
    if ds: entry["steps"] = int(ds.group(1))
    mini = {"title": f"preview {sid}", "channel": "preview", "order": [sid],
            "slides": {sid: entry}, "appendix": None}
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>preview — {sid}</title>
<style>{read(SRC/'tokens.css')}
{read(SRC/'slides.css')}</style></head><body>
<div class="stage"><div class="frame">{frag}
<div id="slide-footer"><span id="slide-num"></span></div>
<div id="apx-overlay"></div><div id="blank-overlay"></div></div></div>
<script>window.DECK_MANIFEST={json.dumps(mini)}; window.DECK_ROLE='audience';</script>
<script>{read(SRC/'state.js')}</script>
<script>{read(SRC/'runtime.js')}</script>
</body></html>"""
    out = ROOT/f"preview-{sid}.html"
    out.write_text(doc, encoding="utf-8")
    print(f"built: {out.name} (standalone; arrows/space step it)")

def sync_manifest():
    """Rewrite manifest slide step-counts from the fragments' data-steps (fragments are authoritative)."""
    mp = ROOT / "manifest.json"
    m = json.loads(read(mp))
    changed = []
    for sid in m["order"]:
        f = FRAG / f"{sid}.html"
        if not f.exists(): continue
        ds = re.search(r'data-steps="(\d+)"', read(f))
        if ds and m["slides"][sid].get("steps") != int(ds.group(1)):
            changed.append(f"{sid}: {m['slides'][sid].get('steps')} -> {ds.group(1)}")
            m["slides"][sid]["steps"] = int(ds.group(1))
    mp.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    print("manifest synced" + (": " + "; ".join(changed) if changed else " (no changes)"))

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        preview(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "--preview":
        sys.exit("usage: build.py --preview <slide-id>")
    elif len(sys.argv) > 1 and sys.argv[1] == "--sync-manifest":
        sync_manifest()
    else:
        build()
