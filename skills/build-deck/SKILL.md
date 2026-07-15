---
name: build-deck
user-invocable: true
argument-hint: "[talk title]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
description: >
  Build a two-window, self-contained presentation: an audience window (clean
  visuals, shared on screen) and a synced presenter console (private talk track,
  pacing clock, step-mapped notes, Q&A prep). Both are single HTML files that run
  from file:// with zero network requests and stay in lock-step. Use this skill
  whenever the user wants to "build a deck", "make slides", "create a presentation",
  "put together a talk", "presenter notes / presenter view", "two-window deck",
  "conference talk slides", "lightning talk", or "turn this script/outline into
  slides". Also produces a stripped, shareable host copy for distribution. Pairs
  well with /thinkkit:create-spec-style rigor: the talk script is a verbatim source
  of truth that automated QA enforces against the presenter notes.
---

# build-deck

Turn a talk into two synced, self-contained windows:

- **`slides.html`** — the audience window. Clean visuals, stepped reveals, shared on screen.
- **`presenter.html`** — your private console. Verbatim talk track with step-mapped highlighting, a pacing clock vs. per-slide budgets, next-slide preview, and a Q&A-prep card the audience never sees.

They sync over a transport-agnostic bus (localStorage + BroadcastChannel + postMessage, id-deduped) that works across two `file://` windows in Arc, Safari, and Chrome regardless of which opened which. Keys work in either window. A third artifact, the **host copy**, is the audience deck with all cross-window JS stripped — safe to send to whoever asks for your slides.

The engine, a full set of slide archetypes, and the reference docs live under `${CLAUDE_PLUGIN_ROOT}/skills/build-deck/assets/` and `.../references/`.

## The core idea: the script is the source of truth

The talk **script** (`script.md`) holds every spoken word. Each slide's presenter notes must quote it **verbatim**; `qa.py` diffs them and fails on any drift. This is the feature that keeps a deck honest as it's edited — visuals and notes can't silently disagree with the talk you rehearsed. Author the script first, or alongside the slides, but always keep notes and script identical sentence-for-sentence.

## Workflow

### Phase 0 — Frame the talk
Ask only what you can't infer: **title, audience, duration, and what raw material exists** (an outline? a full script? just an idea?). Settle the spoken content before touching HTML. If there's no script yet, draft `script.md` from the user's material and get sign-off on the words — everything downstream keys off it. For a high-stakes talk, run the adversarial-persona review in `references/orchestration.md` on the script before building.

### Phase 1 — Scaffold the project
Pick a project dir (default: a `deck/` folder in the user's working area). Copy the engine and a starting set of fragments:

```bash
DECK=<project>/deck
mkdir -p "$DECK/fragments"
cp -r ${CLAUDE_PLUGIN_ROOT}/skills/build-deck/assets/engine/src "$DECK/src"
cp ${CLAUDE_PLUGIN_ROOT}/skills/build-deck/assets/engine/{build.py,dist.py,qa.py} "$DECK/"
cp -r ${CLAUDE_PLUGIN_ROOT}/skills/build-deck/assets/engine/test "$DECK/test"
# archetypes -> starting fragments + a working manifest/script to edit down
cp ${CLAUDE_PLUGIN_ROOT}/skills/build-deck/assets/archetypes/*.html "$DECK/fragments/"
cp ${CLAUDE_PLUGIN_ROOT}/skills/build-deck/assets/archetypes/{manifest.json,script.md} "$DECK/"
```

The archetypes ARE a runnable 7-slide demo deck (`title → chart → table → ladder → timeline → closing → qa`). Build it once immediately to confirm the toolchain works before you change anything (see Phase 4).

### Phase 2 — Plan the slide sequence
Map the script's beats to slides. For each, choose an archetype from `references/authoring-contract.md` (title, chart/spectrum, criteria table, ladder, timeline, checklist/closing, Q&A) or design a custom one against the slide contract. Write `manifest.json`: the `order`, and for each slide its `steps`, `budget` (spoken minutes), and short `title`. Set `script`, `noVerbatim` (usually `["qa"]`), and `budgetTarget` (sum of budgets). Read `references/authoring-contract.md` for the full manifest schema and the slide/notes contract.

### Phase 3 — Author each slide
Every slide is two files:
- **`fragments/<id>.html`** — the visual. A `<section class="slide" data-slide="<id>" data-steps="N">`; elements with `data-step="n"` appear when the current step ≥ n. Scoped `<style>` and inline SVG are fine; **no external URLs, fonts, or scripts** (the build audit fails on any). Design against the tokens and the 960px-viewport rules in `references/design-system.md`.
- **`fragments/<id>-notes.html`** — the talk track. An `<article class="note-card" data-slide="<id>">` of `<p data-step="n"><span class="stepmark" data-step="n">STEP n</span> …</p>` paragraphs whose prose is **verbatim from `script.md`**. Presenter-only asides go in `<span class="cue">[…]</span>` (stripped from the verbatim check).

Keep `data-steps`, the manifest `steps`, and the highest `data-step` in the notes in agreement. When they drift, run `python3 build.py --sync-manifest` (fragments win).

### Phase 4 — Build, QA, eyeball
```bash
cd "$DECK"
python3 build.py            # writes slides.html + presenter.html; audits for external refs
python3 qa.py               # verbatim + structure + stepmark + budget checks; exit 1 on any fail
python3 build.py --preview <id>   # single-slide harness to eyeball one slide's layout/steps
node test/state.test.mjs && node test/integration.test.mjs   # engine sanity (optional)
```
Fix until `qa.py` prints **DECK QA: ALL PASS**. QA is structural, not visual — always open the built files in a real browser at the presenter's actual viewport (often a ~960px-CSS MacBook screen) and step through. Layout bugs hide at that width; `references/design-system.md` documents the ones that recur.

### Phase 5 — Rehearse the two windows
Open `presenter.html`, click **Open audience window** (or open `slides.html` in a second window by hand — sync works either way). Confirm they track: Space/→ advance, ← back, PgUp/PgDn whole slides, Home/End, **B** blank the audience, **C** appendix, **Q** jump to Q&A, **T** start/stop the clock.

### Phase 6 — Ship the host copy
```bash
python3 dist.py   # writes the stripped, shareable standalone (name/title from manifest)
```
This is the audience deck with every cross-window transport removed — inert `send()`, no channel, no listeners, nothing written to localStorage. Fully keyboard-navigable, `file://`-safe. Send this, never `presenter.html`.

## Scaling up: multi-agent build

For a large or high-stakes deck, drive Phases 0–4 with the orchestration recipe in `references/orchestration.md`: adversarial-persona review of the script, then per-slide **plan → implement → verify** teams in parallel, then a composition + whole-deck QA pass. It documents the model-role split, the per-slide agent contract, and the verbatim-fidelity gate.

## References
- `references/authoring-contract.md` — the slide/notes/manifest contract, the archetype catalog, SlideHooks for programmatic slides, and the keymap.
- `references/design-system.md` — design tokens, the palette swap, layout rules, and the 960px-viewport failure modes and fixes.
- `references/orchestration.md` — the multi-agent plan/implement/verify build and the adversarial-persona script review.
