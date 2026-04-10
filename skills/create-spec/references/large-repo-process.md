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
   which to work on this session. Do NOT auto-pick. If all subsystems
   are `complete`, offer to refresh the root spec or exit cleanly.
4. For the chosen subsystem, mark it `in-progress` and deep-spec it
   following Steps 5–8 of this document (scoped to that subsystem).
5. After the pressure test converges, update the manifest: mark the
   subsystem `complete`, record the current commit in `last-spec-commit`,
   and update the root `generated` date.
6. If the user wants to do another subsystem in the same session, return
   to step 3. Otherwise, finalize (Step 10) and exit.

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
