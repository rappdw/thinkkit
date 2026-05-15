---
name: boardroom
user-invocable: true
argument-hint: [decision to debate]
allowed-tools: Read, Write, Bash, Agent, WebSearch, WebFetch
description: >
  Strategic boardroom debate with AI advisors. Use this skill when the user wants to pressure-test
  a decision by having multiple AI-simulated business leaders debate it. Trigger on phrases like
  "boardroom", "get my advisors to debate", "strategic debate", "board of directors", "what would
  X think about", or any request to simulate multiple expert perspectives arguing about a decision.
  Also use when the user says "/thinkkit:boardroom".
---

# Boardroom

Spin up a team of AI advisors — real people whose strategic thinking the user admires — and
have them debate a decision. First a discovery round where advisors ask clarifying questions,
then two debate rounds. The result is a folder of deliverables: a markdown debate transcript,
an interactive HTML with assumption sliders, and a PDF for sharing.

## Setup (First Use)

If no advisors are configured yet, interview the user to build their board. This only needs
to happen once — the advisor profiles persist in `boardroom-config.md` in the current
directory.

### Selecting Advisors

Ask the user:

> Before we run your first boardroom, I need to assemble your board of advisors. A few
> questions:
>
> 1. **What's your business/domain?** (This helps me suggest relevant thinkers)
>
> 2. **How many advisors do you want?** (4-8 works best — enough diversity without noise)
>    - a) 4 — tight, focused debate
>    - b) 6 — good diversity (recommended)
>    - c) 8 — wide range of perspectives
>
> 3. **What kind of board do you want?**
>    - a) Industry experts — people who know your specific domain deeply
>    - b) Cross-domain visionaries — big thinkers from adjacent or unrelated fields
>    - c) Balanced — mix of domain experts, contrarians, and wildcards
>    - d) I have specific people in mind

For each advisor, research and create a profile:
- **Name**
- **Personality profile** (2-3 sentences): how they think, what they prioritize, what biases
  they bring. Be specific — "focuses on unit economics and payback periods" not just "thinks
  about money."
- **Role on the board**: what perspective they uniquely bring (e.g., "the pricing hawk",
  "the customer obsessive", "the platform thinker")

Write profiles to `boardroom-config.md` in the current directory. Example:

```markdown
# Boardroom Advisors

## Business Context
[Brief description of the business — filled in from user interview]

## Advisors

### 1. [Name] — [Role]
[2-3 sentence personality profile]

### 2. [Name] — [Role]
[2-3 sentence personality profile]
```

Also ask if the user has a **business context document** — a markdown file describing their
business, revenue, team, products, goals, and positioning. If so, note the path in the config.
If not, interview them to create a brief one.

## Running a Boardroom Session

When the user invokes `/thinkkit:boardroom [question]`, run the full debate:

### Round 0: Discovery (Parallel)

Before the advisors debate, they need to understand the situation deeply. Spin up one agent
per advisor in parallel. Each agent receives the advisor's profile, business context, and the
question, then generates **2-3 targeted questions** from their specific worldview.

Instruct each agent:

```
You are [Name]. Here is your profile:
[profile]

Here is the business context:
[business context]

The question before the board is: [question]

Before you debate this, what do you need to know? Generate 2-3 specific questions that
would sharpen your position. Ask from YOUR perspective and priorities — a pricing hawk
asks different questions than a platform thinker.

Format each as a single clear question. No preamble, no commentary.
```

Collect all questions, deduplicate where advisors ask essentially the same thing, and
present them to the user grouped by theme:

> Before the advisors debate, they'd like some additional context. A few questions:
>
> **Market & Positioning**
> 1. [Question] *(asked by [Name])*
> 2. [Question] *(asked by [Name] and [Name])*
>
> **Economics**
> 3. [Question] *(asked by [Name])*
>
> **Execution**
> 4. [Question] *(asked by [Name])*
>
> Answer as many as you can — skip any that aren't relevant.

After the user responds, fold their answers into the business context that gets passed to
Rounds 1 and 2. If any answer is surprising or reveals a constraint the advisors wouldn't
have anticipated, note it explicitly in the context so it shapes their positions.

**Optional follow-up probe:** If the user's answers reveal something unexpected — a
constraint, a prior failed attempt, a non-obvious stakeholder — spin up a quick second
pass where 1-2 of the most relevant advisors ask one follow-up question each. Keep this
tight; don't turn discovery into an interrogation.

### Round 1: Initial Positions (Parallel)

Spin up one agent per advisor, all in parallel. Each agent receives:
- The advisor's personality profile
- The business context document (if provided)
- The user's question

Each agent writes their advisor's position:
- **800-1200 words** arguing their position (more or less as needed to convey 95% of their
  point — don't pad, don't truncate prematurely)
- A clear **YES / NO / CONDITIONAL** vote
- **Specific numbers and projections** on cost, revenue, impact, and team joy where relevant
- Written in first person, in the advisor's voice and thinking style

Instruct each agent:

```
You are roleplaying as [Name]. Here is your profile:
[profile]

Here is the business context:
[business context]

The question before the board is: [question]

Write your position in 800-1200 words (more or less as needed). Argue from your specific
worldview and priorities. Include:
- Your YES/NO/CONDITIONAL vote
- Specific numbers, projections, or frameworks that support your position
- What you think the biggest risk is
- What you think everyone else will get wrong

Write in first person as [Name]. Be direct, be specific, be yourself.
```

### Round 2: Rebuttals (Parallel)

Collect all Round 1 positions. Spin up agents again in parallel. Each agent receives all
other advisors' Round 1 positions plus their own.

Each agent writes a **400-800 word rebuttal** that includes:
- **Who they disagree with most** and why, referencing that person's actual argument
  (quote them, name them)
- **Who made them think** — did anyone shift their perspective?
- Whether they **changed their mind** (and if so, why — be specific)
- Their **FINAL vote** (which can differ from Round 1)

Instruct each agent:

```
You are still [Name]. Here is what every advisor argued in Round 1:

[all positions]

Now write your rebuttal (400-800 words). You MUST:
- Name the advisor you disagree with most and quote their actual argument
- Explain why they're wrong or missing something
- Acknowledge if anyone made a point that shifted your thinking
- Give your FINAL vote (YES/NO/CONDITIONAL) — it can change from Round 1

Be direct. This is a debate, not a seminar. If someone said something wrong, call it out.
If someone changed your mind, say so and say why.
```

### Deliverables

Create a folder named after the decision (slugified, e.g., `pricing-25k-vs-50k/`) in the
current directory. Generate three files:

#### 1. `debate.md` — Full Transcript

```markdown
# Boardroom: [Question]
*[Date] — [Number] advisors, 3 rounds (discovery + 2 debate)*

## Discovery Context
[Summary of key facts surfaced in Round 0 — the answers that shaped the debate]

## Vote Tracker

| Advisor | Round 1 | Final | Changed? |
|---------|---------|-------|----------|
| [Name]  | YES     | NO    | Yes      |
| ...     | ...     | ...   | ...      |

**Consensus:** [Unanimous YES / Majority YES / Split / Majority NO / Unanimous NO]

## Key Tensions
- [Tension 1: brief description of the core disagreement]
- [Tension 2]

## Round 1 Positions

### [Name] — [Role]
**Vote: [YES/NO/CONDITIONAL]**
[Full position]

---
[repeat for each advisor]

## Round 2 Rebuttals

### [Name] — [Role]
**Final Vote: [YES/NO/CONDITIONAL]** [Changed from: X]
[Full rebuttal]

---
[repeat for each advisor]

## Decision Framework
[Synthesize the key factors that emerged from the debate into a framework
the user can apply]
```

#### 2. `debate.html` — Interactive Dashboard

Create a self-contained HTML file (all CSS/JS inline) with:
- **Styled cards** for each advisor showing their position summary and vote
- **Vote change visualization** — show Round 1 → Final vote with visual indicators
- **Interactive sliders** for key assumptions that emerged from the debate (price points,
  conversion rates, team size, timeline, etc.) that dynamically recalculate projections
- **Clean, professional styling** — dark header, card layout, readable typography
- Brand it as "Boardroom — Strategic Decision Analysis"

The sliders should update projected numbers in real-time using JavaScript. Identify the
2-5 most important numerical assumptions from the debate and make those the slider inputs.

#### 3. `debate.pdf` — Shareable Summary

Use `synthkit pdf` (or `md2pdf` if available) to convert a print-optimized version of the
debate markdown to PDF. If synthkit is not installed, generate the PDF via pandoc directly,
or note that the user can run `md2pdf debate.md` to create it.

### Synthesis

After generating deliverables, present a synthesis to the user:

> ## Boardroom Results: [Question]
>
> **Final votes:** [tally]
>
> **Who changed their mind:** [names and why]
>
> **Biggest fight:** [the core disagreement, who vs who]
>
> **Sharpest insight:** [the single most valuable point from the debate]
>
> **Likely decision:** [what the debate points toward, with caveats]
>
> Deliverables saved to `[folder]/` — the HTML version has interactive sliders
> to test different assumptions.
