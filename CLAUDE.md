# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Thinkkit is a Claude Code plugin that packages structured thinking methodologies as user-invocable skills. It serves as both a plugin and a marketplace (users add the repo URL directly). There is no build step, test suite, or runtime — skills are Markdown-defined prompt workflows invoked via `/thinkkit:<skill-name>`.

## Repository Layout

- `.claude-plugin/` — Plugin manifest (`plugin.json`) and marketplace registry (`marketplace.json`)
- `skills/<name>/SKILL.md` — Each skill's complete definition (frontmatter + instructions)
- `skills/<name>/references/` — Supporting methodology docs loaded on demand
- `skills/<name>/scripts/` — Executable code (only `map-the-repo/scripts/map.py` currently)

## Development

**Install locally for testing:**
```bash
claude --plugin-dir /path/to/thinkkit
```

**map.py** is the only executable code — Python stdlib only (ast, argparse, json, re, pathlib, dataclasses). No external dependencies.

## Skill Architecture Patterns

Skills fall into distinct workflow patterns. When creating or modifying skills, match the appropriate pattern:

**Multi-agent debate** (boardroom, council, ciso-review): Spawn parallel agents representing different perspectives, then synthesize. `boardroom` and `ciso-review` run multiple rounds into shareable deliverables (`.md` + `.html` + `.pdf`); `council` is the lightweight variant — parallel subagents produce independent first opinions, then anonymized peer review and chairman synthesis happen inline, delivered as an inline answer. These skills declare `Agent` in `allowed-tools` and inherit the session model (no `model:` pin).

**Structured elicitation** (explore-with-me, init-discovery): Interview the user with focused questions before generating anything. The methodology files in `references/` define the interviewing approach. The key discipline is *not* generating analysis upfront — ask first, generate after.

**Iterative analysis** (create-spec, map-the-repo): Deep codebase exploration followed by document generation with pressure-test loops. `map-the-repo` uses a Python script for static analysis; `create-spec` works purely through Claude's tools.

**Session-based capture** (take-notes, resolve-against-transcript): Real-time interaction during or after meetings. `take-notes` expands terse input into notes files under `meeting-notes/`. `resolve-against-transcript` compares a transcript against notes and walks through discrepancies interactively.

**Guided drafting** (press-release): Turn a short brief into a structured deliverable, asking only for the missing essentials rather than running a full interview. `press-release` mines the invoking prompt, fills gaps, and emits a six-section release defined by `references/template.md`, marking assumptions/gaps/unverified stats inline. The methodology lives in `references/` (a `worksheet.md` intake checklist and a `template.md` output structure).

## Skill Frontmatter

Every SKILL.md requires YAML frontmatter with at minimum `name`, `description`, and `user-invocable: true`. The `description` field drives skill triggering — make it specific about when to trigger, and slightly "pushy" (Claude tends to undertrigger). Optional fields: `model`, `allowed-tools`, `argument-hint`.

## Composability

Some skills chain naturally: `take-notes` produces files that `resolve-against-transcript` consumes. `explore-with-me` feeds into `init-discovery` for multi-session projects. When modifying these skills, preserve the file format conventions that enable this chaining (e.g., `meeting-notes/YYYY-MM-DD-<slug>.md` naming, `name: note` speaker attribution format).
