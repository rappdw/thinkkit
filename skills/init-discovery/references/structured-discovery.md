# [Initiative Name] — Project Context

<!-- STRUCTURED DISCOVERY TEMPLATE
     Copy this file, fill in bracketed placeholders, and use as your CLAUDE.md.
     The opening prompt at the bottom kicks off the session.
     See skills/explore-with-me/references/structured-elicitation.md for the method behind this template.
-->

## Initiative Overview

[2-3 paragraphs: what this initiative is, why it exists, who commissioned it,
and what problem it addresses. Write enough that the AI can orient itself in
the domain, but don't over-specify — the discovery process fills in the detail.]

### Current State

- [What exists today — systems, processes, documents, posture]
- [Known pain points or failure signals]
- [What's been tried or is in progress]
- [Known concerns or risks that need careful handling]

### Deliverable

[What this work produces. Be specific:]
1. [Format — memo, slide deck, decision document, architecture proposal]
2. [Audience — who receives it, who else needs to buy in]
3. [Timeline — when it's due]
4. [Nature — is this a diagnosis, a recommendation, a plan, a decision?]

## Key Actors

| Role | Name | Relevance |
|------|------|-----------|
| [Title] | [Name] | [What they own, their authority scope, why they matter] |
| [Title] | [Name] | [What they own, their authority scope, why they matter] |

## Behavioral Instructions

### Drive through questioning, not generation
Use the AskUserQuestion tool abundantly. Drive all sessions through structured
questioning rather than document generation. Surface assumptions, probe blind
spots, challenge framings. The humans on this initiative have the domain
knowledge — the AI's job is to structure the thinking, identify gaps, and
pressure-test reasoning.

### Commit regularly with meaningful messages
Commit to git regularly with meaningful commit messages that capture what was
decided or discovered in each session. Commits are the project's decision trail.

### [Deliverable] lens
Always maintain the lens of "what does the [deliverable] need." Don't let the
work drift into pure analysis without connecting back to the outcome. Every
working session should advance the deliverable.

### Options before conclusions
When ready to explore solutions, create files under `options/` rather than
jumping to conclusions prematurely. The options space needs to be explored and
evaluated before converging on a direction.

<!-- Add domain-specific behavioral instructions as needed. Examples:

### Legal sensitivity awareness
Flag anything that could create legal exposure if documented. Suggest whether
sensitive findings belong in a restricted file vs. general working documents.
When in doubt, ask before writing.

### Technical depth
Push for specifics — architecture diagrams, data flows, failure modes — not
just narrative descriptions.

### Living requirements
Treat `requirements.md` as a living document. Update it as you learn more
about what stakeholders actually need.
-->

## File Structure

| File | Purpose | Sensitivity |
|------|---------|-------------|
| `current-state.md` | What exists today and where it falls short | Internal |
| `problem-analysis.md` | Root cause analysis | Internal |
| `requirements.md` | What stakeholders/customers actually need (living doc) | Internal |
| `options/` | Solution alternatives | Internal |
| `decision-log.md` | Rationale for directions taken or rejected | Internal |
| `[deliverable]-outline.md` | Evolving structure of the final output | Internal |

<!-- Add or remove files to fit your problem. Mark sensitive files explicitly. -->

---

## Opening Prompt

<!-- Paste one of these as your first message to start the discovery session. -->

### General Discovery

```
Let's begin the [initiative name] work. Before we generate any documents or
analysis, I want to make sure we have a sharp problem definition grounded in
reality.

Walk me through a structured discovery conversation. Start with [the most
important starting angle — where the pain is, where the risk is, where the
uncertainty is]. I want to understand the problem from multiple angles before
we touch any of the solution space.

Take it one topic area at a time — don't front-load everything at once.
```

### Architectural Tradeoff Exploration

```
I need to make a decision on [architectural choice]. Before we evaluate options,
walk me through a structured discovery of the constraints and requirements.

Start with [the usage patterns / the failure modes / the integration points] —
I want to make sure we're solving the right problem before we compare solutions.

One topic at a time.
```

### Organizational / Process Analysis

```
We have a [process/organizational] problem around [area]. Before we propose
changes, I want to understand the current state and failure modes clearly.

Walk me through a structured discovery. Start with [where the friction actually
occurs / who's involved / what's been tried]. One topic area at a time.
```

### Risk Assessment

```
I need to assess the risks around [area]. Don't generate a risk register yet —
first walk me through a structured discovery to understand the landscape.

Start with [the most likely failure mode / the highest-stakes area / what we
don't know]. One topic at a time.
```
