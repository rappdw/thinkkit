---
name: create-spec
description: >
  Reverse-engineer any codebase into a reconstruction-grade specification —
  a document thorough enough that a fresh Claude Code session could rebuild
  a functionally equivalent repo from scratch using only the spec. Supports
  both initial creation and incremental updates (detects an existing spec
  and updates only what changed), and scales from small projects to large
  monorepos (triages repo size, asks the user about depth vs. breadth, and
  switches to a hierarchical multi-file spec under `SPECIFICATION/` when
  appropriate, with optional multi-session coverage). Use this skill
  whenever the user asks to "create a spec", "write a specification",
  "update the spec", "reverse-engineer this codebase", "create a blueprint",
  or says anything about producing or refreshing a document that captures
  everything needed to recreate a project. Also trigger when the user wants
  to "snapshot the architecture" or "write a technical spec for this repo".
  Note: this is different from map-the-repo, which generates a browsable
  wiki. This skill produces a reconstruction-grade specification.
user-invocable: true
argument-hint: "[output path, default: SPECIFICATION.md or SPECIFICATION/ for large repos]"
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
---

# Create Specification

Generate a specification that fully captures a repository's behavior,
architecture, and design intent — complete enough that another engineer (or
a fresh Claude Code session) could reconstruct a functionally equivalent
codebase from the spec alone, without ever seeing the original source.
For small/medium repos this is a single `SPECIFICATION.md`; for large
repos it becomes a hierarchical `SPECIFICATION/` directory (see Phase 0.5).

## Why this matters

Code is the "what." A specification captures the "what," "why," and "why not."
When you need to port a project, onboard someone, survive a rewrite, or just
create an insurance policy against losing context, a specification that can
stand on its own is invaluable. The bar is high on purpose: if the spec has
gaps, the rebuild will have bugs.

## Output path

If the user provides an argument, use it as the output path.
Otherwise:

- Small/medium repos → write to `SPECIFICATION.md` in the repository root.
- Large repos → write to the `SPECIFICATION/` directory in the repository
  root (see Phase 0.5 and `references/large-repo-process.md`).

## Required sections

The specification must include all of the following. Each section should be
detailed enough that someone could implement it without ambiguity.

### 1. Purpose and Architecture Overview
- What the project does, who it's for, and what problem it solves
- High-level architecture diagram (ASCII or Mermaid)
- Key architectural patterns (MVC, event-driven, microservices, etc.)
- How components communicate with each other

### 2. Module Organization and Responsibilities
- Logical decomposition: what modules/components exist and what each owns
- Dependency direction between modules (what depends on what, and why)
- Boundaries: what's internal vs. exposed, what's generated vs. hand-authored
- Any organizational constraints the architecture imposes (e.g., plugins must
  live in a specific structure, or modules must be self-contained)

### 3. Public Interfaces
- Every API endpoint (method, path, request/response schemas, status codes)
- CLI commands with all flags, arguments, and expected behavior
- Configuration schemas (all fields, types, defaults, validation rules)
- Environment variables and their effects
- Exported functions/classes intended for external consumption

### 4. Data Models and State Management
- Every data model with field types, constraints, and relationships
- Database schemas or storage layout
- State management approach (where state lives, how it flows)
- Migration strategy if applicable

### 5. Key Algorithms and Business Logic
- Pseudo-code for any non-trivial algorithm
- Business rules and validation logic
- Processing pipelines and data transformations
- Concurrency or async patterns

### 6. Capabilities and External Integrations
- What capabilities the project requires from external libraries or services
  (e.g., "needs an HTTP framework with middleware support," "needs a YAML parser")
- External services or APIs the system integrates with and how
- Runtime requirements (language version, platform constraints)
- Any capability where the specific choice matters and why (e.g., "must use
  libsodium-compatible encryption for interop with X")

### 7. Build, Test, and Run Instructions
- Step-by-step build process
- How to run the test suite and what it covers
- Development server / local run instructions
- Required system prerequisites

### 8. Design Decisions and Constraints
- Decisions that were made AND alternatives that were rejected, with reasoning
- Known limitations or trade-offs
- Performance characteristics and scaling considerations
- Security model and trust boundaries

### 9. Edge Cases and Error Handling
- Error handling patterns used throughout the codebase
- Known edge cases and how they're handled
- Retry/fallback strategies
- Input validation approach

### 10. Implementation Gaps and Opportunities
The deep review required to write this spec will surface issues that aren't
visible from a casual read. Capture them here, categorized by type:

- **Test coverage gaps** — untested paths, missing edge-case tests, modules
  with no tests at all
- **Security risks** — unvalidated input, missing auth checks, exposed secrets,
  unsafe defaults, trust boundary violations
- **Performance concerns** — inefficient algorithms, N+1 queries, missing
  caching, unbounded growth, blocking operations in hot paths
- **Reliability issues** — missing error handling, silent failures, no retry
  logic where needed, race conditions
- **Dead code and tech debt** — unused modules, deprecated patterns still in
  use, TODO/FIXME items that warrant attention
- **Missing documentation** — undocumented public interfaces, implicit
  conventions that should be explicit

For each item, note what it is, where it is, and the potential impact.
Prioritize by severity — security and correctness issues first, then
reliability, then performance, then cleanup.

## Process

This is an iterative process. Rushing produces a spec with gaps, and gaps
defeat the entire purpose. The pressure-test loop is what separates a useful
spec from a superficial one.

### Phase 0: Detect Mode (Create vs. Update)

Before doing anything else, check whether a specification already exists.
Check both possible layouts:

- **Single-file layout**: `SPECIFICATION.md` in the repo root (or the
  user-provided path).
- **Hierarchical layout**: a `SPECIFICATION/` directory containing
  `index.md` and `manifest.json` (used for large repos — see Phase 0.5
  and `references/large-repo-process.md`).

**If no existing spec is found** → proceed to Phase 0.5.

**If a single-file spec is found**, switch to incremental update mode:

1. Read the existing spec. Extract the commit hash from its metadata header.
2. Run `git diff <spec-commit>..HEAD --stat` to identify what files/modules
   have changed since the spec was generated. If no commit hash is present,
   fall back to a full review but still preserve unchanged sections.
3. Scope your exploration (Phase 1) to the changed areas and their
   immediate dependents — modules that import from or interact with
   what changed.
4. In Phase 2, update only the affected sections of the existing spec
   rather than rewriting from scratch. Preserve sections that haven't
   changed, including any manual refinements the user may have added.
5. In Phase 3, run the pressure-test loop scoped to the updated sections,
   but do one final pass across section boundaries to catch interaction
   effects (e.g., a changed interface that invalidates an unchanged
   algorithm description).
6. Update the metadata header with the new commit hash and date.

**If a hierarchical spec is found**, load `references/large-repo-process.md`
and follow its multi-session resume flow (Step 9). Do not fall through to
Phase 0.5 — the tier has already been decided.

### Phase 0.5: Scale Triage

Before starting exploration on a fresh spec, measure the repository:

1. Count source files. Prefer `git ls-files` filtered to source extensions;
   fall back to `find` if not a git repo. Exclude vendor/build/dist dirs.
2. Count top-level modules using build-file heuristics: directories
   containing any of `package.json`, `pom.xml`, `build.gradle`,
   `Cargo.toml`, `go.mod`, `pyproject.toml`, `*.csproj`, `*.sln`,
   `CMakeLists.txt`, `BUILD`, `BUILD.bazel`.
3. Note language distribution (extension counts).

**Classification:**

- **Small/medium** — <2,000 source files AND ≤10 top-level modules
  → proceed to Phase 1 with the standard single-file flow. Output goes
  to `SPECIFICATION.md`.

- **Large** — ≥2,000 source files OR >10 top-level modules
  → load `references/large-repo-process.md` and follow it from Step 1.
  Do NOT begin exploration until the user has picked a tier. The
  large-repo flow produces a hierarchical spec under `SPECIFICATION/`
  (kept separate from source) and may span multiple sessions.

### Phase 1: Deep Exploration

Before writing anything, thoroughly explore the codebase:

1. Read the project's README, CLAUDE.md, package.json (or equivalent manifest)
2. Identify the logical modules and understand what each is responsible for
3. Identify entry points (main files, index files, CLI entry points)
4. Trace the critical paths through the code
5. Read test files — they reveal intended behavior and edge cases
6. Check configuration files for implicit behavior
7. Review git history for context on recent design decisions (if available)

Spend real effort here. Read the actual source files, don't just skim
file names. The quality of the spec depends entirely on how well you
understand the codebase.

### Phase 2: Write the Initial Draft

Write the full specification covering all required sections. Be specific:
use actual type names, actual field names, actual endpoint paths. Vague
hand-waving ("the system handles errors appropriately") is a gap. For
hierarchical mode, this draft spans the root `index.md` and each
`subsystems/<name>.md` — see `references/large-repo-process.md` Steps 5–7.

### Phase 3: Pressure Test (at least 2 iterations)

This is the critical quality step. For each iteration:

**Step 1 — Gap detection (without re-reading source):**
Go through each section of the spec and ask: "Could I actually implement this
module from what's written here?" Flag every ambiguity, missing detail, or
assumption that isn't spelled out. Be adversarial — look for:
- Missing return types or error conditions
- Implicit ordering dependencies
- Configuration that's mentioned but not fully specified
- Algorithms described in prose that need pseudo-code
- Interactions between components that aren't documented

**Step 2 — Resolve gaps (go back to source):**
For each flagged gap, re-read the relevant source code and extract the
missing detail.

**Step 3 — Update the spec:**
Incorporate all resolved gaps into SPECIFICATION.md.

**Step 4 — Final validation:**
Walk through the codebase and confirm that every significant behavior,
contract, and design decision is captured in the spec. Focus on behavioral
completeness — could someone implement each module's responsibilities from
what's written? List any remaining gaps.

**Termination condition:**
Stop iterating when the gap list from Step 4 is empty OR contains only
cosmetic items (variable names, comment style, whitespace formatting).

### Phase 4: Finalize and Integrate

After the pressure test loop converges, write the final clean version of
SPECIFICATION.md. Include a metadata header at the top:

```
<!-- spec-meta: { "generated": "YYYY-MM-DD", "commit": "<short-hash>", "iterations": N } -->
```

This metadata enables incremental updates (Phase 0) in future runs.

**CLAUDE.md integration:** After writing the spec, check whether a CLAUDE.md
exists in the repository root. If it does, and it does not already mention
the specification, append a Specification section.

For single-file (small/medium) specs, use:

```markdown
## Specification

This repository has a machine-generated specification at `SPECIFICATION.md`
(or the custom path). When making implementation changes, update the
corresponding sections of the specification to keep it in sync. Run
`/thinkkit:create-spec` to perform an incremental update.
```

For hierarchical (large-repo) specs, use the variant in
`references/large-repo-process.md` Step 10, which points at
`SPECIFICATION/index.md`, the `subsystems/` directory, and the manifest.

If no CLAUDE.md exists, add a brief maintenance note to the top of the
root spec (just below the metadata header):

```markdown
> **Maintenance:** When the implementation changes, re-run
> `/thinkkit:create-spec` to incrementally update this document.
```

## Style guidelines

- Be precise and concrete, not vague and abstract
- Use code blocks for schemas, types, pseudo-code, and command examples
- Use tables for structured data (API endpoints, config fields, etc.)
- Prefer showing over telling: an example request/response pair is worth
  more than a paragraph of description
- Keep the tone technical and neutral
- Use Mermaid diagrams for architecture and data flow where they add clarity
- Mark any intentional simplifications with a note explaining what was omitted
