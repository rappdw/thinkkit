# Large Repository Specification Process

This document defines how `create-spec` handles repositories too large for
a single-session, single-file specification. It is loaded on demand from
SKILL.md when Phase 0.5 classifies a repo as "large" (≥2,000 source files
OR >10 top-level modules), or when Phase 0 detects an existing hierarchical
spec.

At scale, reconstruction-grade coverage cannot be delivered in one session
at one level of depth. The user must decide the depth/breadth trade-off
before exploration begins.

## Step 1: Present scale summary and tier choice

After measuring the repo in Phase 0.5, present a concise summary and the
tier menu to the user. Do not proceed until they pick a tier.

Template:

> This repository has **<N>** source files across **<M>** top-level modules
> (<language breakdown>). A single `SPECIFICATION.md` at reconstruction-grade
> depth is not achievable in one session. How would you like me to proceed?
>
> 1. **Architectural-only** (single file) — shape, boundaries, build
>    topology, design intent. No deep interface capture. One session.
>
> 2. **Architectural + targeted drilldowns** (single file) — same as (1),
>    plus deep specs for 2–5 subsystems you name. One session.
>
> 3. **Hierarchical, single session** — root spec + per-subsystem specs
>    under `SPECIFICATION/`. Subsystems explored in parallel via Explore
>    subagents. Depth capped by context budget; I'll flag any shallow
>    subsystems in the output.
>
> 4. **Hierarchical, multi-session** — root spec + manifest this session.
>    You re-run `/thinkkit:create-spec` to deepen each subsystem one at
>    a time. Highest fidelity for monorepos.
>
> 5. **Proceed with full depth anyway** — accept that the session may
>    not converge.

Wait for the user's response.

## Step 2: Output layout by tier

**Tiers 1 and 2** use the single-file layout — same as the small-repo flow,
writing to `SPECIFICATION.md` in the repo root.

**Tiers 3 and 4** use the hierarchical layout, kept entirely separate from
source code:

```
SPECIFICATION/
  index.md                  # root spec — architecture, subsystem index,
                            # build topology, cross-cutting concerns
  manifest.json             # coverage tracking
  subsystems/
    <subsystem-name>.md     # per-subsystem reconstruction-grade spec
```

Never intermingle spec files with source directories. `SPECIFICATION/` is
the single home for all spec content.

## Step 3: Subsystem discovery (hybrid)

For tiers 2, 3, and 4, you need a refined list of subsystems. Use the
hybrid approach:

**Heuristic pass (cheap):**
- Find directories containing build/project files: `package.json`,
  `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, `pyproject.toml`,
  `*.csproj`, `*.sln`, `CMakeLists.txt`, `BUILD`, `BUILD.bazel`.
- Each such directory is a candidate subsystem boundary.
- If no build files surface a clean structure, fall back to top-level
  source directories.

**Refinement pass (Claude judgment):**
- Group closely-related candidates (e.g., 50 similar microservices under
  a single "services" umbrella, or a family of C++ libraries that share
  a common purpose).
- Split overly-broad candidates that mix unrelated concerns.
- Assign a short slug name and a one-line summary to each final subsystem.
- Present the refined list to the user for confirmation before deep work
  begins. The user may edit, merge, or split further.

A good subsystem count for a large repo is typically 8–20. Fewer means
each spec is too broad; more means root-level coherence is lost.

## Step 4: Manifest format

Create `SPECIFICATION/manifest.json` after the subsystem list is confirmed:

```json
{
  "generated": "YYYY-MM-DD",
  "commit": "<short-hash>",
  "tier": "hierarchical-single-session",
  "priority-order": ["billing", "auth", "ingestion"],
  "subsystems": [
    {
      "name": "billing",
      "path": "services/billing",
      "status": "pending",
      "spec": "subsystems/billing.md",
      "last-spec-commit": null,
      "summary": "Handles invoicing, payment processing, and subscription lifecycle"
    }
  ]
}
```

**Status values:**
- `pending` — identified but not yet spec'd
- `in-progress` — being spec'd in the current session (transient)
- `complete` — spec written and pressure-tested
- `stale` — spec exists but source has changed since `last-spec-commit`

**Tier values:**
- `hierarchical-single-session` — tier 3
- `hierarchical-multi-session` — tier 4

Update the manifest every time a subsystem's status changes.

`priority-order` is optional for the default single-pick flow. It is
required to enable the autonomous loop mode in Step 9.5; if absent when
the user opts into the loop, the skill derives a candidate order
(roughly: foundational / most-depended-on first) and asks the user to
confirm or edit before entering the loop.

## Step 5: Root spec content (SPECIFICATION/index.md)

The root spec covers everything that is NOT subsystem-local. Its sections
mirror the 10-section structure from SKILL.md, but scoped to cross-cutting
concerns:

1. **Purpose and Architecture Overview** — top-level picture of the whole
   repo and how subsystems relate
2. **Module Organization and Responsibilities** — the confirmed subsystem
   list with one-paragraph summaries and links to per-subsystem specs
3. **Public Interfaces** — only interfaces exposed at the repo boundary
   (external APIs, top-level CLIs). Subsystem-internal interfaces belong
   in the subsystem spec.
4. **Data Models and State Management** — only cross-subsystem data
   contracts (shared models, event schemas, common database tables)
5. **Key Algorithms and Business Logic** — only cross-cutting algorithms
   (distributed coordination, shared pipelines)
6. **Capabilities and External Integrations** — platform-wide runtime,
   build system, shared infrastructure
7. **Build, Test, Run Instructions** — repo-wide build topology and
   orchestration
8. **Design Decisions and Constraints** — architectural decisions that
   apply across subsystems
9. **Edge Cases and Error Handling** — cross-cutting error models, retry
   patterns, observability conventions
10. **Implementation Gaps and Opportunities** — architectural-level gaps
    only; subsystem-local gaps belong in subsystem specs

Include the metadata header and the subsystem index prominently near the
top:

```markdown
<!-- spec-meta: { "generated": "YYYY-MM-DD", "commit": "<hash>", "tier": "...", "iterations": N } -->

## Subsystems

| Name | Path | Status | Spec |
|---|---|---|---|
| billing | services/billing | complete | [subsystems/billing.md](subsystems/billing.md) |
| auth    | services/auth    | pending  | —                                              |
```

## Step 6: Per-subsystem specs

Each `subsystems/<name>.md` follows the standard 10-section structure from
SKILL.md, scoped to that subsystem. Omit sections that don't apply — for
example, a library subsystem has no "Build, Test, Run" of its own; defer
to the root spec.

Sections 3 (Public Interfaces), 4 (Data Models), and 5 (Algorithms) are
typically the deepest in a subsystem spec.

Each subsystem spec gets its own metadata header so incremental updates
can target it individually:

```markdown
<!-- spec-meta: { "subsystem": "billing", "generated": "YYYY-MM-DD", "commit": "<hash>", "iterations": N } -->
```

## Step 7: Parallel exploration (tier 3)

For hierarchical-single-session, delegate each subsystem's initial
exploration to an `Agent` call with `subagent_type: Explore`. Each agent
returns a focused summary: entry points, public interfaces, key data
models, notable algorithms, gaps observed.

Run agents in parallel by issuing multiple Agent tool calls in a single
response. This is the only practical way to cover many subsystems without
burning main context on file-by-file reads.

Each subagent prompt should:
- Name the subsystem and its path
- Reference the standard 10-section structure
- Ask for a bounded summary (≤500 lines) suitable for the main session to
  turn into a full spec
- Flag any observed implementation gaps (Section 10 material)
- Request specific file paths and line numbers for any referenced code

The main session then synthesizes each summary into a subsystem spec and
runs its own pressure-test pass over the result.

## Step 8: Pressure test, scoped

Run the pressure-test loop (from SKILL.md Phase 3) **per subsystem**, not
once over the whole spec. After every subsystem has converged, do a
**cross-cutting pass** to catch contract mismatches — e.g., an interface
described one way in subsystem A's spec and differently in subsystem B's.
This cross-cutting pass is what the root spec's inter-subsystem contract
section should reflect.

## Step 9: Multi-session resume (tier 4 re-invocation)

When Phase 0 detects an existing `SPECIFICATION/manifest.json`, follow
this flow instead of Phase 0.5:

1. Read the manifest and load its subsystem list.
2. For each `complete` subsystem, run
   `git diff <last-spec-commit>..HEAD -- <path>`. If there are any
   changes, mark the subsystem `stale` in the manifest.
3. Show the user a numbered list of all non-`complete` subsystems with
   their current status (`pending`, `stale`, `in-progress`), and ask
   which to work on this session. Do NOT auto-pick unless the user has
   explicitly opted into loop mode (Step 9.5) — in that case, selection
   is driven by `priority-order` and no prompt is shown. If all
   subsystems are `complete`, offer to refresh the root spec or exit
   cleanly.
4. For the chosen subsystem, mark it `in-progress` and deep-spec it
   following Steps 5–8 of this document (scoped to that subsystem).
5. After the pressure test converges, update the manifest: mark the
   subsystem `complete`, record the current commit in `last-spec-commit`,
   and update the root `generated` date.
6. If the user wants to do another subsystem in the same session, return
   to step 3 — or, in loop mode, re-enter the Step 9.5 ritual for the
   next `priority-order` entry without prompting. Otherwise, finalize
   (Step 10) and exit.

## Step 9.5: Autonomous Multi-Subsystem Loop (opt-in)

By default, multi-session resume (Step 9) requires the user to pick one
subsystem at a time. For users who want to power through the whole
priority list in a single long-running session, this step defines an
opt-in loop mode. It must never activate implicitly — the user has to
ask.

### Activation conditions

All three must hold:

1. A `SPECIFICATION/manifest.json` exists (loop mode only applies to
   hierarchical specs that already exist).
2. The user has explicitly opted in — e.g., passed `--loop` as the
   skill argument, or said something like "do them all," "run the whole
   list," "power through every subsystem," or "loop through the
   priority order."
3. The manifest contains a `priority-order` array (Step 4). If it does
   not, derive a candidate order from the subsystem list, present it
   to the user, and get explicit confirmation before entering the loop.

If any of (1)–(3) is missing and cannot be resolved, fall back to Step
9's default single-pick flow.

### Per-subsystem ritual

Every iteration performs the same atomic, idempotent ritual. Automatic
context compaction may fire between iterations — or mid-iteration — so
every step must be safe to re-enter from a fresh read of the manifest:

1. **Re-read the manifest from disk.** Do not trust any in-conversation
   memory of "what's next." The manifest on disk is the only source of
   truth.
2. **Select the next target.** Walk `priority-order` and pick the first
   subsystem whose status is not `complete`. If an `in-progress` entry
   exists, resume that one rather than starting a new one. If none
   remain, exit the loop.
3. **Emit the iteration header** (see "Progress messages" below).
4. **Mark `in-progress`** in the manifest and update the session task
   list.
5. **Shard exploration.** Measure the subsystem. If it has >10 projects
   OR >500 source files, split it into ≤3 concern groups (chosen by the
   main session from the subsystem's layout — e.g., "ingestion
   pipeline," "admin API," "shared models") and dispatch one
   `Agent(subagent_type: Explore)` per group in a single response so
   they run in parallel. Otherwise dispatch a single Explore agent.
   Never exceed 3 parallel agents — the goal is bounded main-context
   pressure, not maximum parallelism.
6. **Synthesize the full 10-section spec** into
   `SPECIFICATION/subsystems/<name>.md`, following Step 6's structure
   and metadata header format.
7. **Pressure test** per Step 8, scoped to this subsystem.
8. **Finalize atomically.** In one burst of writes: flip the manifest
   status to `complete`, stamp `last-spec-commit` with the current
   short hash, update the subsystem row in `SPECIFICATION/index.md`'s
   subsystem table, mark the task completed.
9. **Emit the finalization message** (see below).
10. **Advance.** Return to step 1 of this ritual. Do not ask the user.

Because step 1 always re-reads the manifest, a compaction that drops
conversation history mid-loop resumes correctly: the next iteration
discovers the current `in-progress` subsystem and either completes it
or (if finalize already landed) picks up the next `priority-order`
entry.

### Sharding heuristic (detail)

Size measurement uses the same build-file + source-file counts as
Phase 0.5 of SKILL.md, scoped to the subsystem's `path`:

- ≤10 projects AND ≤500 source files → 1 Explore agent, whole subsystem
- otherwise → 2 or 3 agents, sharded by concern group

If a clean concern split isn't obvious, default to 2 agents: one
covering public interfaces + entry points, one covering data models +
internal algorithms.

### Stop conditions

Exit the loop cleanly when any of these fires:

- **All done.** No `priority-order` entries remain non-`complete`.
  Fall through to Step 10 (CLAUDE.md integration) and exit.
- **User interrupt.** Any user message during the loop stops it.
  Finish the current atomic step — do not abandon a half-written spec
  or an inconsistent manifest — then stop and await instructions.
- **Convergence failure.** A subsystem fails to converge in Step 8's
  pressure test twice in a row (two full iterations with the gap list
  not shrinking). Mark the subsystem `stale` with an added
  `loop-blocked: true` flag in its manifest entry, print an escalation
  line, and stop. Do not auto-advance past a failure.

### Progress messages

Before each iteration, emit a single-line header:

```
[3/16] billing — sharded into 2 Explore agents
```

Format: `[<index>/<total>] <slug> — sharded into <K> Explore agent(s)`
where `<total>` is `len(priority-order)` and `<index>` is the 1-based
position of the current subsystem within it.

After finalization, emit:

```
[3/16] billing complete — SPECIFICATION/subsystems/billing.md written, manifest updated
```

On stop-condition exit, emit exactly one of:

```
Loop complete — all 16 subsystems finalized.
Loop paused — user interrupt at [7/16] ingestion.
Loop halted — [9/16] auth failed to converge after 2 pressure-test rounds; marked stale, loop-blocked.
```

### Guardrails

Loop mode does not relax the base prompt's "careful actions" rules.
Inside the loop:

- **No git commits, no pushes, no tags, no force operations.** Even if
  the user opted into the loop, they did not opt into shared-state
  writes.
- **File writes are restricted to `SPECIFICATION/`** (subsystem specs,
  `index.md`, `manifest.json`) plus the session task list. Nothing
  else in the repo.
- **No destructive file operations** anywhere.

If a ritual step appears to require any of the above, stop the loop
and ask the user.

## Step 10: CLAUDE.md integration (large-repo variant)

After finishing work in a session, update the repo's CLAUDE.md (or add
the section if CLAUDE.md exists but lacks it):

```markdown
## Specification

This repository has a machine-generated specification under `SPECIFICATION/`.
The root spec is `SPECIFICATION/index.md`; per-subsystem specs live in
`SPECIFICATION/subsystems/`. Coverage is tracked in
`SPECIFICATION/manifest.json`.

When making implementation changes, update the corresponding subsystem spec
(or the root spec if the change is cross-cutting). Run
`/thinkkit:create-spec` to refresh — it will detect which subsystems are
stale and offer to update them.
```

If no CLAUDE.md exists, place a similar maintenance note at the top of
`SPECIFICATION/index.md` just below the metadata header.
