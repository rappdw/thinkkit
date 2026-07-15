#!/usr/bin/env python3
"""Produce a standalone, shareable copy of the AUDIENCE deck for distribution.

Run from a deck project root (holds manifest.json, src/, fragments/).

All cross-window (presenter-sync) JavaScript is removed: outbound send() is a
no-op, no BroadcastChannel is opened, and there are no inbound message/storage
listeners. The result is fully navigable by keyboard (arrows/space/PgUp-PgDn/
Home/End/B/C), reveals steps and runs any SlideHooks, deep-links via the URL
hash, writes nothing to localStorage, and never looks for another window.

Manifest keys read here:
  title      (str) deck title
  distTitle  (str, optional) <title> for the host copy; default = title
  distName   (str, optional) output filename; default derived from title

Usage: python3 dist.py   ->  writes the distribution HTML beside slides.html
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC, FRAG = ROOT / "src", ROOT / "fragments"

def read(p): return Path(p).read_text(encoding="utf-8")

def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s).strip()
    return re.sub(r"[\s_]+", "-", s) or "presentation"


def strip_sync(rt):
    """Neutralize every cross-window transport in runtime.js."""
    header_old = """/* Shared runtime for both windows. Expects globals injected at build time:
     window.DECK_MANIFEST  — parsed manifest.json
     window.DECK_ROLE      — 'presenter' | 'audience'

   SYNC DESIGN (transport-agnostic bus; no dependency on window.open):
   Messages travel over every available transport — (1) opener/child postMessage
   when a window relationship exists, (2) BroadcastChannel where the browser
   allows it, (3) localStorage 'storage' events, which fire across any two
   windows of the same origin (including file:// in Chromium/Arc/Safari).
   Every message carries a unique id; receivers dedupe, so multi-transport
   delivery is harmless.

   AUTHORITY MODEL: the presenter is the source of truth. The audience window
   applies its own keys locally (so it also works standalone for rehearsal)
   AND broadcasts them as intents; the presenter applies intents and pushes
   absolute state, which the audience always adopts. The protocol converges
   regardless of which transports are alive. */"""
    header_new = """/* Standalone audience deck (distribution copy).
   Cross-window presenter sync has been removed: this file navigates purely
   from its own keyboard handlers and writes to no shared transport. */"""

    send_old = """  function send(msg) {
    msg.src = ROLE;
    msg.id = uid();
    remember(msg.id); // never process our own message echoed back
    if (ROLE === 'presenter' && audienceWin && !audienceWin.closed) {
      try { audienceWin.postMessage(msg, '*'); } catch (e) {}
    }
    if (ROLE === 'audience' && window.opener && !window.opener.closed) {
      try { window.opener.postMessage(msg, '*'); } catch (e) {}
    }
    if (bc) { try { bc.postMessage(msg); } catch (e) {} }
    try { localStorage.setItem(LSKEY, JSON.stringify(msg)); } catch (e) {}
  }"""
    send_new = "  function send() { /* standalone copy: cross-window presenter sync removed */ }"

    bc_old = """  var bc = null;
  try { bc = new BroadcastChannel(CH); } catch (e) { bc = null; }"""
    bc_new = "  var bc = null; /* standalone copy: no cross-window channel opened */"

    listeners_old = """  window.addEventListener('message', function (e) { onMessage(e.data); });
  if (bc) bc.onmessage = function (e) { onMessage(e.data); };
  window.addEventListener('storage', function (e) {
    if (e.key !== LSKEY || !e.newValue) return;
    try { onMessage(JSON.parse(e.newValue)); } catch (err) {}
  });"""
    listeners_new = "  /* standalone copy: no inbound cross-window listeners */"

    for old, new, label in (
        (header_old, header_new, "header comment"),
        (send_old, send_new, "send()"),
        (bc_old, bc_new, "BroadcastChannel"),
        (listeners_old, listeners_new, "inbound listeners"),
    ):
        if old not in rt:
            sys.exit(f"strip_sync: could not find {label} block — runtime.js changed; update dist.py")
        rt = rt.replace(old, new)
    return rt


def main():
    m = json.loads(read(ROOT / "manifest.json"))
    title = m.get("title", "Presentation")
    dist_title = m.get("distTitle", title)
    out_name = m.get("distName") or f"{slugify(title)}-slides.html"
    tokens, slides_css = read(SRC / "tokens.css"), read(SRC / "slides.css")
    state_js = read(SRC / "state.js")
    runtime_js = strip_sync(read(SRC / "runtime.js"))
    manifest_js = "window.DECK_MANIFEST = " + json.dumps(m) + ";"

    frags = []
    for sid in m["order"]:
        f = FRAG / f"{sid}.html"
        if not f.exists():
            sys.exit(f"missing fragment: {f}")
        frags.append(read(f))
    apx_html = ""
    if m.get("appendix"):
        ap = FRAG / f"{m['appendix']}.html"
        if ap.exists():
            apx_html = read(ap)

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{dist_title}</title>
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

    leaks = []
    for pat in (r'src="https?://', r'href="https?://', r'url\(\s*[\'"]?https?://', r'@import', r'fetch\('):
        if re.search(pat, doc):
            leaks.append(pat)
    if leaks:
        sys.exit("EXTERNAL REFERENCES FOUND:\n  " + "\n  ".join(leaks))

    residue = []
    for tok in ("localStorage", "BroadcastChannel(", "window.opener", "postMessage",
                "addEventListener('storage'", 'addEventListener("storage"', "addEventListener('message'"):
        if tok in doc:
            residue.append(tok)
    if residue:
        sys.exit("SYNC RESIDUE FOUND (presenter-linking not fully stripped):\n  " + "\n  ".join(residue))

    out = ROOT / out_name
    out.write_text(doc, encoding="utf-8")
    print(f"built: {out.name} ({len(doc):,} bytes)")
    print("audit: zero external references; zero cross-window sync surface")


if __name__ == "__main__":
    main()
