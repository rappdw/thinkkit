---
name: tutorial
description: >
  Interactive tutorial for the thinkkit plugin. Walks new users through every
  skill in the plugin with concrete examples, explains when to use each one,
  and shows how skills chain together. Use this skill whenever the user asks
  for a "thinkkit tutorial", "how do I use thinkkit", "what can thinkkit do",
  "show me thinkkit", "getting started with thinkkit", "introduce me to
  thinkkit", or says they just installed thinkkit and want to learn it. Also
  trigger on phrases like "teach me the thinking tools", "what skills are in
  this plugin", or "give me a tour".
user-invocable: true
allowed-tools: Read
---

# Thinkkit Tutorial

Welcome the user to thinkkit and give them a guided tour of the plugin. The
goal is to leave them confident about which skill to reach for when, with a
concrete example they could run in the next five minutes.

## Your role

You are a tour guide, not a lecturer. Don't dump the full contents of every
SKILL.md on them. Figure out what they actually want to use, then go deep on
that. Keep the pace conversational.

## Step 1: Orient them

Open with a brief framing, then find out where to go:

> Thinkkit is a collection of structured thinking tools. There are nine
> skills organized into four patterns. Rather than walk through all of them,
> let me point you at what's most useful for your situation.
>
> What brought you here?
>
> 1. I have a decision to make and want to pressure-test it (quick gut-check or formal debate)
> 2. I'm evaluating a vendor, product, or my own security posture
> 3. I need to work through a complex problem or explore a topic
> 4. I need to document or understand a codebase
> 5. I'm about to go into a meeting and want help capturing it
> 6. Just give me the full tour

Based on their answer, go to the appropriate section below. If they pick
"full tour," cover all four patterns in sequence with less depth per skill.

## The four patterns

Skills in thinkkit fall into four patterns. Use these as your mental map:

**Multi-agent debate** — Spawn several AI perspectives that argue with each
other, then synthesize. For pressure-testing decisions and reviews.
*Skills: `boardroom`, `council`, `ciso-review`*

**Structured elicitation** — Interview the user with focused questions
before generating anything. The discipline is asking first, writing after.
*Skills: `explore-with-me`, `init-discovery`*

**Iterative analysis** — Deep code exploration followed by document
generation with pressure-test loops.
*Skills: `map-the-repo`, `create-spec`*

**Session-based capture** — Real-time or post-meeting note handling.
*Skills: `take-notes`, `resolve-against-transcript`*

## Skill-by-skill walkthroughs

For each skill the user is interested in, cover these four things: what it
does, when to reach for it, a concrete example command, and what output
they'll get. Keep each to a few paragraphs.

### boardroom — Pressure-test a decision through simulated advisors

**What it does:** Assembles a board of AI-simulated advisors (real people
whose thinking you respect) and has them debate a decision in two rounds.
First round: each advisor writes their position independently. Second round:
they read each other's arguments and write rebuttals, sometimes changing
their votes.

**When to reach for it:** You're facing a decision where you suspect you're
anchored, missing perspectives, or about to commit to something significant.

**Try this:**
```
/thinkkit:boardroom should we raise a Series B in Q2 or extend runway with a bridge?
```

**What you get:** A folder with `debate.md` (full transcript), `debate.html`
(interactive dashboard with sliders for key assumptions), and `debate.pdf`.
Plus a synthesis showing who changed their mind and the sharpest insight
that emerged.

**First-time setup:** The skill will interview you once to build your board
of advisors (4-8 people whose thinking you respect). That config persists.

---

### council — Fast multi-angle gut-check

**What it does:** Convenes a small council of advisors — each a distinct
*thinking lens* rather than a named person — to answer one question. Several
independent agents answer first, then critique each other's answers blind,
then a chairman synthesizes a verdict with concrete next steps. It's a
faithful adaptation of Andrej Karpathy's LLM Council.

**When to reach for it:** You want other angles on something *right now*,
without setup or ceremony. The lighter, faster cousin of boardroom — no
advisor config, no deliverables, answer delivered inline.

**Try this:**
```
/thinkkit:council should I rewrite this service in Go or keep patching the Python one?
```

**What you get:** An inline verdict — the call, the reasoning that survived
peer review, where the council split, and a "Monday morning" list of next
steps. Optionally saved to a `council-*.md` transcript if you want a record.

**council vs. boardroom:** Use council for a fast informal read with thinking
lenses; use boardroom for a formal debate with real-world advisors and
shareable artifacts.

---

### ciso-review — Enterprise security assessment

**What it does:** Adopts the persona of a skeptical CISO and evaluates
either a vendor/product you're considering adopting, OR your own approach
through the eyes of an enterprise CISO who would evaluate it during
procurement. Eight evaluation domains plus hard questions the vendor would
hate to answer.

**When to reach for it:** Two modes. Vendor evaluation: "should we adopt
Acme Vault?" Self-assessment: "will our approach pass a CISO review, and
what's the GTM impact?"

**Try this:**
```
/thinkkit:ciso-review evaluate Supabase for storing our customer PII
```
or
```
/thinkkit:ciso-review pressure-test our new AI feature's security story for enterprise buyers
```

**What you get:** An `assessment.md`, `assessment.html` (risk heatmap), and
`assessment.pdf`. Includes an APPROVE/CONDITIONAL/REJECT recommendation,
hard questions, and (in self-assessment mode) buyer archetype analysis and
GTM impact.

---

### explore-with-me — Structured thinking partner

**What it does:** Runs a depth-first interview to help you think through a
problem. Asks 2-3 questions per round on one topic, probes surprising
answers, validates its synthesis with you before writing anything.

**When to reach for it:** You have a problem where you hold the domain
knowledge and need someone to structure your thinking — diagnosing an issue,
making a hard call, postmortems, risk assessments. Anything where premature
generation would be worse than discovering the right framing first.

**Try this:**
```
/thinkkit:explore-with-me why are our evaluation pipelines so fragile
```

**What you get:** After 5-15 rounds of interviewing, a markdown file
capturing context, key findings, constraints, tensions, and recommendations.

---

### init-discovery — Scaffold a multi-session investigation

**What it does:** The multi-session version of explore-with-me. Creates a
CLAUDE.md and working file structure for a discovery project that will span
days or weeks. Interviews you to populate the project template.

**When to reach for it:** A single exploration session won't cut it. You're
setting up a sustained investigation (architectural redesign, organizational
analysis, risk assessment) that needs to persist across sessions.

**Try this:**
```
/thinkkit:init-discovery authentication architecture redesign
```

**What you get:** A CLAUDE.md with initiative overview, current state,
deliverable definition, key actors, and behavioral instructions, plus
working files (`current-state.md`, `problem-analysis.md`, `requirements.md`,
`options/`, `decision-log.md`). You then continue with subsequent sessions
against that scaffold.

---

### map-the-repo — Generate a browsable wiki from a codebase

**What it does:** Runs a Python static analysis script, then enriches the
generated scaffolding with architectural insight. Produces both markdown
docs and a self-contained HTML site with search and Mermaid diagrams.

**When to reach for it:** You need to document a codebase, onboard someone
to a project, or build a browsable wiki. Best used on codebases you want
others to explore, not just snapshot.

**Try this:**
```
/thinkkit:map-the-repo .
```

**What you get:** `wiki/docs/*.md` (architecture, data flows, API reference,
glossary, per-module docs) and `wiki/site/index.html` (browsable with dark
theme, search, diagrams). The skill checks whether LSP language servers are
available and offers to install them for better analysis.

---

### create-spec — Reconstruction-grade specification

**What it does:** Reverse-engineers a repo into a single SPECIFICATION.md
document complete enough that a fresh Claude Code session could rebuild a
functionally equivalent codebase from the spec alone. Uses at least two
pressure-test iterations to flag and resolve gaps.

**When to reach for it:** Different goal than map-the-repo. Use this when
you need a single document that captures everything — for a port, a rewrite,
an insurance policy against losing context, or preparing an LLM to
reconstruct the system.

**Try this:**
```
/thinkkit:create-spec
```

**What you get:** A SPECIFICATION.md at the repo root with nine required
sections (purpose, directory structure, public interfaces, data models,
algorithms, dependencies, build/test/run, design decisions, edge cases).

**Difference from map-the-repo:** map-the-repo generates a browsable wiki
for exploration; create-spec generates a single spec for reconstruction.

---

### take-notes — Real-time meeting notes

**What it does:** You feed it terse, shorthand observations during a meeting,
and it expands each entry into clear prose and maintains a running document
with Notes, Action Items, and Open Questions sections.

**When to reach for it:** You're about to join a meeting and want Claude to
handle the note-taking while you stay focused on the conversation.

**Try this:**
```
/thinkkit:take-notes Q4 planning review
```

Then during the meeting, send messages like:
- `dan: adapter layer needs rethink before next sprint`
- `concerns about kong throughput for v2`
- `action: mariano to draft the migration plan by friday`

**What you get:** A file at `meeting-notes/YYYY-MM-DD-<title>.md` that
updates in real time. Speaker attribution is opt-in via `name:` prefix —
unattributed entries are captured as observations.

---

### resolve-against-transcript — Reconcile notes with recording

**What it does:** Given a meeting transcript and a notes file, identifies
discrepancies (factual errors, mischaracterizations, attribution errors,
missing content, missing action items) and walks through resolving each one
interactively.

**When to reach for it:** You took notes in a meeting (or someone else did)
and now have the recording transcript. You want to verify the notes are
accurate before distributing them.

**Try this:**
```
/thinkkit:resolve-against-transcript recording.vtt meeting-notes/2026-04-05-q4-planning.md
```

**What you get:** An interactive loop that shows you each discrepancy with
the transcript excerpt, the current notes text, a proposed fix, and
accept/modify/skip options. Plus a summary at the end.

## Compositions worth knowing

The skills chain naturally. Point the user at these when relevant:

**Meeting workflow:** `take-notes` during → `resolve-against-transcript`
after. Take shorthand notes live, reconcile against the transcript later.

**Discovery workflow:** `explore-with-me` for quick explorations →
`init-discovery` when a single session won't cut it → use the resulting
CLAUDE.md as project context for all subsequent sessions.

**Documentation workflow:** `map-the-repo` when you need a wiki for others
to browse; `create-spec` when you need a single reconstruction-grade
document. They're complementary, not redundant.

**Strategy workflow:** `explore-with-me` to surface the right framing →
`council` for a fast multi-angle gut-check, or `boardroom` for a formal
debate → `ciso-review` if there's an adoption/security dimension.

## Closing

After walking through the skills they cared about, invite them to try one:

> Want to try one now? Pick the skill that matches your most immediate need.
> I can help you set it up or run it together.

If they're still deciding, suggest `explore-with-me` — it's the lowest-stakes
starting point and often surfaces which of the other skills would help next.
