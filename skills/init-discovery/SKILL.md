---
name: init-discovery
user-invocable: true
argument-hint: [project name]
allowed-tools: Read, Write, Bash
description: >
  Scaffold a multi-session structured discovery project. Use this skill when the user wants to
  set up a new exploration initiative, create a CLAUDE.md for a discovery project, or start a
  sustained investigation that will span multiple sessions. Trigger on phrases like "set up a
  discovery project", "init discovery", "scaffold an exploration", "I have a big problem to
  work through over multiple sessions", or "/thinkkit:init-discovery". This is the multi-session
  counterpart to /thinkkit:explore-with-me — use explore-with-me for single-session explorations and
  init-discovery when the work will span days or weeks.
---

# Init Discovery

This skill scaffolds a multi-session structured discovery project by interviewing the user
and generating a customized `CLAUDE.md` plus working file structure.

Before starting, read [references/structured-discovery.md](references/structured-discovery.md)
— it defines the template sections you need to fill in.

## How It Works

You are filling in a project template, but the way you fill it in is itself a structured
discovery. Walk through the template sections in order, asking focused questions to draw out
what goes in each one. Don't ask the user to "fill in the blanks" — interview them and write
the content yourself based on their answers.

## Session Flow

### 1. Initiative Overview (2-3 questions)

Start here. You need to understand what this project is about.

> Let's set up your discovery project. First, a few questions about the initiative:
>
> 1. **What's the initiative or problem area?** Give me a short name and a sentence or two.
>
> 2. **What kind of work is this?**
>    - a) Diagnosing a problem (something isn't working)
>    - b) Making a strategic decision (choosing a direction)
>    - c) Building a plan or proposal (shaping what to do next)
>    - d) Assessing risk (understanding what could go wrong)
>    - e) Something else

Based on their answers, draft 2-3 paragraphs for the Initiative Overview section. Show it
to them for confirmation before moving on.

### 2. Current State (2-3 questions)

> Now let me understand where things stand today:
>
> 1. **What exists right now?** (systems, processes, documents, prior work)
> 2. **What are the known pain points or failure signals?**
> 3. **What's already been tried or is in progress?**

Synthesize into bullet points. Confirm.

### 3. Deliverable (2-3 questions)

> Let's define what this work produces:
>
> 1. **What's the output format?**
>    - a) A decision document
>    - b) A memo or briefing
>    - c) An architecture proposal
>    - d) A plan with action items
>    - e) Something else
>
> 2. **Who's the audience?** (who receives it, who else needs to buy in)
>
> 3. **When is it due?** And is this a hard deadline or a target?

### 4. Key Actors (1-2 questions)

> Who are the key people involved? For each, I need their role, name, and what they own or
> why they matter to this work.

Build the actors table. Confirm.

### 5. Behavioral Instructions (1-2 questions)

The template includes default behavioral instructions (drive through questioning, commit
regularly, maintain deliverable lens, options before conclusions). Ask if any need adjusting
or if domain-specific instructions should be added:

> The project will use these default working principles:
> - Drive through questioning, not generation
> - Commit regularly with meaningful messages
> - Always maintain the deliverable lens
> - Explore options before jumping to conclusions
>
> **Should I add any domain-specific instructions?** For example:
> - a) Legal sensitivity awareness (flag things that could create exposure if documented)
> - b) Technical depth (push for architecture diagrams, data flows, failure modes)
> - c) Stakeholder management (track who needs to be consulted on what)
> - d) These defaults are fine
> - e) Something else

### 6. File Structure (1 question)

Show the default file structure from the template and ask if it fits:

> Here's the default working file structure:
>
> | File | Purpose |
> |------|---------|
> | `current-state.md` | What exists today and where it falls short |
> | `problem-analysis.md` | Root cause analysis |
> | `requirements.md` | What stakeholders actually need (living doc) |
> | `options/` | Solution alternatives |
> | `decision-log.md` | Rationale for directions taken or rejected |
> | `[deliverable]-outline.md` | Evolving structure of the final output |
>
> **Does this fit your project, or should I adjust?**

### 7. Validate and Write

Assemble the full CLAUDE.md from all confirmed sections. Show a summary of what you're
about to create, then:

1. Write `CLAUDE.md` to the current directory
2. Create the working files and directories (empty, with a one-line heading describing
   their purpose)
3. Pick the most appropriate opening prompt from the template (General Discovery,
   Architectural Tradeoff, Organizational/Process, or Risk Assessment) and suggest it to
   the user as their first message for the next session

Tell the user:
> Your discovery project is set up. Here's what I created:
> - `CLAUDE.md` — project context and behavioral instructions
> - [list of working files/dirs]
>
> To start your first discovery session, use this as your opening message:
> [suggested opening prompt, customized with their initiative details]
