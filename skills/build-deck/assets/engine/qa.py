#!/usr/bin/env python3
"""Whole-deck structural QA. Run from a deck project root, after build.py. Exit 1 on any failure.

Every check degrades gracefully: give the manifest key and the check runs; omit it and the
check is skipped (reported as such). Nothing here is talk-specific.

Optional manifest keys:
  script         (str)  path (relative to project root) to the verbatim talk script.
                        When present, every spoken notes paragraph must appear in it verbatim.
  noVerbatim     (list) slide ids to exclude from the verbatim check (e.g. ["qa"]).
  budgetTarget   (num)  expected sum of per-slide budgets (excluding noVerbatim slides).
                        When present, the sum must match within 0.01.
  animatedSlides (list) slide ids permitted to define @keyframes. When present, keyframes
                        anywhere else fail the build. When absent, no restriction.
"""
import re, html, json, sys
from pathlib import Path

ROOT = Path(__file__).parent            # deck project root (this script sits at project root)
m = json.loads((ROOT/"manifest.json").read_text())
slides_doc = (ROOT/"slides.html").read_text()
pres_doc = (ROOT/"presenter.html").read_text()
fail = []

no_verbatim = set(m.get("noVerbatim", []))

# 1) verbatim: spoken text in notes (with .cue spans REMOVED first) must appear in the script
if m.get("script"):
    script_path = (ROOT / m["script"]).resolve()
    if not script_path.exists():
        fail.append(f"manifest 'script' path not found: {m['script']}")
        print("verbatim: SCRIPT NOT FOUND")
    else:
        script = re.sub(r'\s+', ' ', script_path.read_text())
        total = 0
        for sid in m["order"]:
            if sid in no_verbatim: continue
            nf = ROOT/f"fragments/{sid}-notes.html"
            if not nf.exists(): continue
            notes = re.sub(r'<span class="cue">.*?</span>', '', nf.read_text(), flags=re.S)
            for i, p in enumerate(re.findall(r'<p[^>]*>\s*<span class="stepmark"[^>]*>STEP \d+</span>\s*(.*?)\s*</p>', notes, re.S), 1):
                txt = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', p)).strip())
                total += 1
                if txt and txt not in script:
                    fail.append(f"{sid} P{i} not verbatim: {txt[:90]}")
        print(f"verbatim: {total} spoken paragraphs -> {'PASS' if not any('not verbatim' in f for f in fail) else 'FAIL'}")
else:
    print("verbatim: skipped (no manifest 'script')")

# 2) presenter-only content must not leak into VISUAL fragments (scan fragments, not built JS)
for sid in m["order"]:
    frag = (ROOT/f"fragments/{sid}.html").read_text()
    for marker in ["armed, not volunteered", "Overrun plan", "[FILL", "stepmark", "note-card", "improvise"]:
        if marker in frag: fail.append(f"{sid}.html contains presenter-only marker: {marker!r}")
print("presenter-leak scan (visual fragments): done")

# 3) structure: sections, cards, steps consistency
sid_map = dict(re.findall(r'data-slide="([\w-]+)"[^>]*data-steps="(\d+)"', slides_doc))
cards = re.findall(r'class="note-card" data-slide="([\w-]+)"', pres_doc)
for sid in m["order"]:
    if sid not in sid_map: fail.append(f"missing slide section: {sid}")
    elif int(sid_map[sid]) != m["slides"][sid]["steps"]: fail.append(f"{sid}: manifest {m['slides'][sid]['steps']} != fragment {sid_map[sid]}")
    if sid not in cards: fail.append(f"missing note card: {sid}")
print(f"structure: {len(sid_map)} sections / {len(cards)} cards for {len(m['order'])} slides")

# 4) stepmark bounds
for sid in m["order"]:
    nf = ROOT/f"fragments/{sid}-notes.html"
    if not nf.exists(): continue
    marks = [int(x) for x in re.findall(r'stepmark" data-step="(\d+)"', nf.read_text())]
    if marks and max(marks) > m["slides"][sid]["steps"]: fail.append(f"{sid}: stepmark {max(marks)} > steps")
print("stepmark bounds: done")

# 5) animation: keyframes confined to manifest.animatedSlides (if that key is present)
if "animatedSlides" in m:
    allowed = set(m["animatedSlides"])
    for sid in m["order"]:
        kf = re.findall(r'@keyframes\s+([\w-]+)', (ROOT/f"fragments/{sid}.html").read_text())
        if kf and sid not in allowed: fail.append(f"{sid}: unexpected @keyframes {kf}")
    print("animation: keyframes confined to animatedSlides -> " + ("ok" if not any('@keyframes' in f for f in fail) else "ISSUES"))
else:
    print("animation: unrestricted (no manifest 'animatedSlides')")

# 6) budget sum
content = sum(m["slides"][s].get("budget", 0) for s in m["order"] if s not in no_verbatim)
if "budgetTarget" in m:
    if abs(content - m["budgetTarget"]) > 0.01: fail.append(f"budget sum {content} != target {m['budgetTarget']}")
    print(f"budget sum: {content} min (target {m['budgetTarget']})")
else:
    print(f"budget sum: {content} min (no target set)")

print("\n" + ("DECK QA: ALL PASS" if not fail else "DECK QA FAILURES:\n  " + "\n  ".join(fail)))
sys.exit(1 if fail else 0)
