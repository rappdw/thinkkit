# Multi-agent build

For a large or high-stakes deck, don't author twelve slides in one context. Fan the work out: review the script adversarially, build each slide with an independent plan → implement → verify team, then compose and run whole-deck QA. This is the recipe that produced the reference deck; scale it down for a lightning talk, up for a keynote.

Two ways to run it:
- **Inline agents** — spawn the teams with the `Agent` tool (subagents in parallel). Good default.
- **`Workflow` tool** — if the user has opted into workflow orchestration, encode the phases as a script (pipeline over slides, verify stage per slide). Only when explicitly requested.

## Model-role split

The split that worked, most-capable model where judgment matters:

| Role | Model | Why |
|------|-------|-----|
| Plan (per slide) | `claude-fable-5` | Decide the visual, the steps, the layout risk |
| Implement (per slide) | `claude-sonnet-5` | Write the fragment + notes to the contract |
| Verify (per slide) | `claude-opus-4-8` | Adversarially check contract, verbatim, 960px risk |
| Composition + whole-deck QA | `claude-fable-5` | Stitch, resolve cross-slide consistency, run `qa.py` |

Omit model overrides and everything inherits the session model — fine for a quick build. Use the split when quality matters more than tokens.

## Phase A — Adversarial script review (before any HTML)

The script is the product; review it before building slides around it. Spawn 3–5 **critical audience personas** (the skeptic, the practitioner who'll actually adopt it, the domain expert who'll catch an overclaim, the newcomer who needs the vocabulary). Each reads `script.md` and returns: a 0–100 "did it land" score, the two weakest moments, and the single change with the highest payoff. Apply the improvements that recur across personas. Re-run once if the script changed materially.

This is where overclaims, missing definitions, and a weak close get caught — cheaply, in prose, before they're encoded in twelve slides.

## Phase B — Per-slide teams (parallel)

One team per slide, teams run concurrently, each team runs plan → implement → verify in order:

**Plan** (input: the slide's script beats, its manifest entry, the archetype catalog). Output a short spec: which archetype or custom layout, the step-by-step reveal plan, the specific 960px risks to avoid, and the exact spoken paragraphs (verbatim from `script.md`) that the notes must carry.

**Implement** (input: the plan). Write `fragments/<id>.html` and `fragments/<id>-notes.html` to the authoring contract. Notes prose verbatim from the script. No external references. Scoped CSS. Return both files.

**Verify** (input: both files + the plan + the script). Adversarially check, and return PASS/FAIL with reasons:
- Notes prose is verbatim in `script.md` (the gate — fail on any drift).
- `data-slide` matches; `data-steps` == manifest `steps` == max notes `data-step`.
- No `https://` / web font / `url(http…)` / `fetch` / `@import`.
- Every CSS rule scoped to `[data-slide="<id>"]`; no `@keyframes` unless the slide is in `animatedSlides`.
- Layout survives a ~960px-wide frame (call out the risks from `design-system.md`).
Loop implement→verify until PASS.

Structured-output schema for the verify stage keeps the loop deterministic:
```json
{ "pass": true, "verbatim_ok": true, "contract_ok": true,
  "no_external_refs": true, "viewport_risks": ["…"], "fixes_needed": ["…"] }
```

## Phase C — Composition + whole-deck QA

One composition pass (fable): assemble `manifest.json` (order, steps, budgets, `budgetTarget` = sum, `script`, `noVerbatim`, `channel`), resolve cross-slide consistency (recurring vocabulary, color meaning, callback beats), write `presenter-ref.html`, then:

```bash
python3 build.py && python3 qa.py
```

`qa.py` is the backstop that no single slide team can see: it diffs **every** spoken paragraph against the script at once, checks structure and stepmark bounds across the whole deck, and confirms the budget sums to target. Fix until **DECK QA: ALL PASS**, then a human eyeballs the built windows at the real viewport (QA is structural, never visual). Ship the host copy with `python3 dist.py`.

## Guardrails

- **The verbatim gate is non-negotiable.** If a slide team wants to reword a line, it edits `script.md` too — never let notes and script diverge. `qa.py` will catch it, but catching it in the verify stage is cheaper.
- **Sensitivity is the author's job, not the engine's.** For an external talk, the script review must scrub names, internal detail, and unshippable claims *before* Phase B. No tool checks this.
- **Don't over-parallelize a small deck.** Under ~6 slides, a single careful pass beats the coordination overhead. Reserve the full fan-out for decks where breadth or stakes justify it.
