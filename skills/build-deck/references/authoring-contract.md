# Authoring contract

Everything the build needs from you, precisely. Author to this and the toolchain does the rest.

## The three kinds of file

A deck project is:

```
deck/
  manifest.json          # the registry (below)
  script.md              # verbatim spoken source of truth
  src/                   # the engine — do not edit (state.js, runtime.js, *.css)
  build.py dist.py qa.py # the tools — do not edit
  test/                  # engine tests — do not edit
  fragments/
    <id>.html            # one visual per slide
    <id>-notes.html      # one talk-track card per slide
    presenter-ref.html   # presenter-only Q&A/overrun card (optional)
    apx.html             # appendix overlay, shown on the C key (optional)
```

## manifest.json

```jsonc
{
  "title": "…",              // audience window <title>
  "presenterTitle": "…",     // optional; presenter window <title>
  "distTitle": "…",          // optional; host-copy <title> (default = title)
  "distName": "…-slides.html",// optional; host-copy filename (default from title)
  "channel": "my-deck",      // sync channel — make it UNIQUE per deck so two decks
                             //   open at once don't drive each other
  "script": "script.md",     // optional; enables the verbatim QA gate
  "noVerbatim": ["qa"],      // optional; slide ids excluded from verbatim (usually just qa)
  "budgetTarget": 14,        // optional; QA asserts the budget sum equals this
  "animatedSlides": ["s5"],  // optional; if present, @keyframes are allowed ONLY on these
  "order": ["title","chart","…","qa"],   // slide order == fragment ids
  "appendix": "apx",         // fragment id shown on C, or null
  "slides": {
    "title": { "steps": 2, "budget": 1, "title": "Cold open" }
    // steps  = number of reveal stops (matches data-steps in the fragment)
    // budget = spoken minutes for pacing (0 for qa)
    // title  = short label shown in the presenter console
  }
}
```

Keep three things in agreement for every slide: the fragment's `data-steps`, the manifest `steps`, and the highest `data-step` used in the notes. `python3 build.py --sync-manifest` rewrites manifest step-counts from the fragments if they drift.

## The visual fragment — `<id>.html`

```html
<section class="slide" data-slide="chart" data-steps="3">
  <h1>…</h1>
  <div data-step="1">… appears at step 1 …</div>
  <div data-step="2">… appears at step 2 …</div>
  <div data-step="3">… appears at step 3 …</div>
  <style> [data-slide="chart"] .whatever { … } </style>   <!-- scope every rule to your slide -->
</section>
```

Rules:
- The `data-slide` value **must equal** the manifest id and the `-notes.html` `data-slide`.
- An element with `data-step="n"` gets the class `on` once the current step ≥ n. Style the hidden/shown states in `slides.css` conventions (opacity/transform transitions are already wired; you just toggle presence with `data-step`).
- Scope all CSS to `[data-slide="<id>"]` so slides can't bleed into each other.
- **No external references.** No `https://`, no web fonts, no `url(http…)`, no `fetch`, no `@import`. Inline SVG and data-URIs only. The build audit fails on any of these.
- `@keyframes` are allowed only on slides listed in `animatedSlides` (when that key is set). Prefer step-driven CSS transitions over keyframe loops; reserve keyframes for one deliberately animated slide.

## The notes fragment — `<id>-notes.html`

```html
<article class="note-card" data-slide="chart">
  <span class="cue">[Presenter-only aside — stripped from the verbatim check.]</span>
  <p data-step="1"><span class="stepmark" data-step="1">STEP 1</span> Exactly the words from script.md, step 1.</p>
  <p data-step="2"><span class="stepmark" data-step="2">STEP 2</span> Exactly the words from script.md, step 2.</p>
</article>
```

Rules:
- The prose inside each `<p data-step>` (after tags are stripped) must appear **verbatim** in `script.md`. `qa.py` collapses whitespace and unescapes entities, then requires a substring match. Edit the notes and the script together, always.
- `<span class="cue">[…]</span>` is for staging asides (what's on screen, when to pause). It is removed before the verbatim check — never put spoken words in a cue, never put staging in a spoken `<p>`.
- The presenter console highlights each `<p>` as its step arrives, so one `<p>` per step (or per spoken beat within a step) reads best.

## Programmatic slides — SlideHooks

For a slide that needs JS beyond declarative step reveals (canvas, layout that must be measured, staged glows), register hooks. The runtime calls them in the audience window:

```html
<script>
  window.SlideHooks = window.SlideHooks || {};
  window.SlideHooks["myslide"] = {
    onEnter: function (step) { /* slide became active at `step` */ },
    onStep:  function (step) { /* step changed while active */ },
    onExit:  function () { /* slide left — tear down timers, etc. */ }
  };
</script>
```

Keep hooks idempotent and cheap; `onStep` can fire repeatedly. Anything a hook needs must be inline (no network). If you use `@keyframes` here, add the slide id to `animatedSlides`.

## Archetype catalog

Copyable, viewport-tested starting points in `../assets/archetypes/`:

| Archetype | File | Steps | Use for |
|-----------|------|-------|---------|
| Title / cold open | `title.html` | 2 | Cover; the one-sentence why + your credential |
| Spectrum / chart | `chart.html` | 3 | Positioning a landscape on axes; "ask where it sits" |
| Criteria table | `table.html` | 3 | A fit test scored live; a candidate that fails one row |
| Ladder | `ladder.html` | 2 | Maturity/autonomy/adoption stages; "you are here" |
| Timeline | `timeline.html` | 4 | A case-study arc with a payoff bracket |
| Closing | `closing.html` | 2 | A checklist that stays + a three-line spoken closer |
| Q&A | `qa.html` | 1 | The slide that persists through Q&A; a resource line |

Each has a matching `-notes.html`. `presenter-ref.html` and `apx.html` are presenter-only/appendix templates.

## Keymap (both windows)

`Space` / `→` advance · `←` back · `PgDn`/`↓` next slide · `PgUp`/`↑` prev slide · `Home`/`End` first/last · `B` blank the audience · `C` toggle appendix · `Q` jump to Q&A · `T` start/stop the pacing clock.

The presenter is authoritative: its keypresses push absolute state to the audience. The audience applies keys locally too (so it rehearses standalone) and forwards them as intents. The host copy from `dist.py` keeps local keys but drops all cross-window messaging.
