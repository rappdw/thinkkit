# Structured Elicitation

A method for using AI as an interviewer rather than a generator. The human holds domain knowledge; the AI structures the thinking, controls sequencing, identifies gaps, and pressure-tests assumptions before anything gets written down.

## When to Use

- **The human knows more than the AI** — organizational analysis, architectural tradeoffs in a specific system, strategy formation, risk assessment, incident postmortems
- **Premature generation is dangerous** — legal-sensitive work, politically charged situations, anything where writing the wrong thing down creates risk or anchors thinking too early
- **The problem has hidden structure** — where the real issue isn't obvious and needs to be uncovered through probing (e.g., what looks like a process problem turns out to be a substance problem)

## When Not to Use

- Pure execution tasks where requirements are already clear
- Problems with well-known solution patterns that don't need discovery

## Core Mechanics

### 1. Progressive Depth, Not Breadth

Ask 2-3 questions on one topic area, then pivot based on what you learn. Don't front-load 15 questions across all dimensions. Each round of answers should inform the next round of questions.

**Why:** Broad surveys get shallow answers. Depth-first exploration surfaces the non-obvious — the contradictions, the unstated assumptions, the things the human knows but hasn't connected to the problem yet.

### 2. Multiple-Choice with Escape Hatches

Offer structured options (2-4 choices) for each question, but always allow free-text alternatives. The options serve two purposes:
- Reduce cognitive load on the human (recognition over recall)
- Surface the AI's mental model so the human can correct it

**Why:** Open-ended questions like "tell me about your data handling" produce rambling answers. "Is the concern X, Y, or Z?" produces precise signal — including when the answer is "none of those, it's actually W."

### 3. Probe the Surprising Answers

When an answer contradicts the obvious hypothesis, that's the most important signal. Pivot immediately to explore why.

**Example:** If the hypothesis is "evaluations fail because there's no process" and the human says "actually, there IS a defined process" — the next question must be "then why is it failing?" That pivot revealed the real root cause (substance risk, not process gaps).

### 4. Summarize and Validate Before Writing

After each major topic area (or after the full discovery), synthesize findings into a structured summary and ask the human to confirm, correct, or add nuance. Only then write to documents.

**Why:** Writing creates anchoring. If the synthesis is wrong, everything built on it drifts. The checkpoint costs 30 seconds and prevents hours of rework.

### 5. One Discovery, Multiple Outputs

The same discovery conversation can populate multiple working documents. Map answers to their destinations as you go — problem definition, requirements, stakeholder analysis, risk register — rather than running separate discovery sessions for each.

## Anti-Patterns

- **The brain dump prompt** — "Tell me everything about X." Produces overwhelming, unstructured responses that the AI then has to sort through.
- **Leading questions** — "Don't you think the problem is X?" Confirms the AI's hypothesis instead of testing it.
- **Generating before discovering** — Writing analysis documents based on assumptions, then asking the human to correct them. This anchors on the AI's framing rather than the human's reality.
- **Treating all answers equally** — Some answers are routine confirmations. Others are revelations that should reshape the entire line of questioning. The AI must recognize the difference and adjust.

## Session Structure

A typical structured elicitation session follows this arc:

1. **Orient** (1-2 rounds) — Establish the basic landscape: where is the problem, who's involved, what's the scope
2. **Diagnose** (2-4 rounds) — Probe the failure modes, root causes, and dynamics. This is where surprising answers emerge
3. **Contextualize** (1-2 rounds) — Understand constraints, stakeholders, authority, timeline — the factors that shape what solutions are feasible
4. **Validate** (1 round) — Summarize findings, get human confirmation
5. **Capture** (write) — Commit validated findings to working documents

The number of rounds scales with problem complexity, but the arc stays the same.
