---
name: create-spec
description: >
  Reverse-engineer any codebase into a complete SPECIFICATION.md — a document
  thorough enough that a fresh Claude Code session could rebuild a functionally
  equivalent repo from scratch using only the spec. Use this skill whenever
  the user asks to "create a spec", "write a specification", "reverse-engineer
  this codebase", "create a blueprint", or says anything about producing a
  document that captures everything needed to recreate a project. Also trigger
  when the user wants to "snapshot the architecture" or "write a technical spec
  for this repo". Note: this is different from map-the-repo, which generates a
  browsable wiki. This skill produces a single reconstruction-grade specification.
user-invocable: true
argument-hint: "[output path, default: SPECIFICATION.md]"
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
---

# Create Specification

Generate a SPECIFICATION.md that fully captures a repository's behavior,
architecture, and design intent — complete enough that another engineer (or
a fresh Claude Code session) could reconstruct a functionally equivalent
codebase from the spec alone, without ever seeing the original source.

## Why this matters

Code is the "what." A specification captures the "what," "why," and "why not."
When you need to port a project, onboard someone, survive a rewrite, or just
create an insurance policy against losing context, a specification that can
stand on its own is invaluable. The bar is high on purpose: if the spec has
gaps, the rebuild will have bugs.

## Output path

If the user provides an argument, use it as the output file path.
Otherwise, write to `SPECIFICATION.md` in the repository root.

## Required sections

The specification must include all of the following. Each section should be
detailed enough that someone could implement it without ambiguity.

### 1. Purpose and Architecture Overview
- What the project does, who it's for, and what problem it solves
- High-level architecture diagram (ASCII or Mermaid)
- Key architectural patterns (MVC, event-driven, microservices, etc.)
- How components communicate with each other

### 2. Directory Structure with Rationale
- Full directory tree with explanations for non-obvious organization choices
- Which directories are generated vs. hand-authored
- File naming conventions

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

### 6. Dependencies
- Every dependency with version constraints
- Why each dependency was chosen (what it provides)
- Any pinned versions and the reason for pinning

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

## Process

This is an iterative process. Rushing produces a spec with gaps, and gaps
defeat the entire purpose. The pressure-test loop is what separates a useful
spec from a superficial one.

### Phase 1: Deep Exploration

Before writing anything, thoroughly explore the codebase:

1. Read the project's README, CLAUDE.md, package.json (or equivalent manifest)
2. Map the directory structure and understand the organization
3. Identify entry points (main files, index files, CLI entry points)
4. Trace the critical paths through the code
5. Read test files — they reveal intended behavior and edge cases
6. Check configuration files for implicit behavior
7. Review git history for context on recent design decisions (if available)

Spend real effort here. Read the actual source files, don't just skim
file names. The quality of the spec depends entirely on how well you
understand the codebase.

### Phase 2: Write the Initial Draft

Write the full SPECIFICATION.md covering all required sections. Be specific:
use actual type names, actual field names, actual endpoint paths. Vague
hand-waving ("the system handles errors appropriately") is a gap.

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
Walk through every source file in the repo and confirm that every behavioral
detail is captured in the spec. List any remaining gaps.

**Termination condition:**
Stop iterating when the gap list from Step 4 is empty OR contains only
cosmetic items (variable names, comment style, whitespace formatting).

### Phase 4: Write the Final Document

After the pressure test loop converges, write the final clean version of
SPECIFICATION.md. Include a brief note at the top indicating:
- When the spec was generated
- What commit/state it reflects
- The number of pressure-test iterations performed

## Style guidelines

- Be precise and concrete, not vague and abstract
- Use code blocks for schemas, types, pseudo-code, and command examples
- Use tables for structured data (API endpoints, config fields, etc.)
- Prefer showing over telling: an example request/response pair is worth
  more than a paragraph of description
- Keep the tone technical and neutral
- Use Mermaid diagrams for architecture and data flow where they add clarity
- Mark any intentional simplifications with a note explaining what was omitted
