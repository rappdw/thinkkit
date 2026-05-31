---
name: council
user-invocable: true
argument-hint: [question or decision to put to the council]
allowed-tools: Read, Write, Agent
description: >
  Convene an LLM council to pressure-test a question or decision. Use this skill when the user
  wants a fast, multi-perspective gut-check — several independent advisors answer the same
  question from different thinking lenses, critique each other's answers blind, and a chairman
  synthesizes a final call with clear next steps. Trigger on phrases like "council", "convene a
  council", "ask the council", "get a few perspectives on this", "what would different advisors
  say", "stress-test this decision", "I'm too close to this — give me other angles", or any
  request for a quick round of diverse opinions on a question. Based on Andrej Karpathy's LLM
  Council. Also use when the user says "/thinkkit:council". For a heavier, formal debate with
  named real-world advisors and shareable deliverables, use /thinkkit:boardroom instead.
---

# Council

Convene a small council of advisors to answer one question from several independent angles,
have them critique each other blind, then synthesize a single clear answer. The point is to
escape the trap where an AI just agrees with you 49% more than a person would — by forcing
genuinely different perspectives into the room and making them compete before you hear a
verdict.

This is a faithful adaptation of [Andrej Karpathy's LLM Council](https://github.com/karpathy/llm-council),
which runs the same three stages across multiple real models. Here we run it inside Claude
Code: independent subagents stand in for independent models, and distinct thinking lenses
stand in for distinct advisors.

## When to use this vs. boardroom

Thinkkit has two multi-perspective skills. Reach for the right one:

- **council** (this skill) — fast, informal gut-check. No setup, runs end-to-end in one shot,
  answer delivered inline. Advisors are *thinking lenses*, not real people. Best for "give me
  other angles on this" before you've committed to anything heavy.
- **boardroom** — formal strategic debate. One-time advisor setup, discovery interview, two
  debate rounds, and a folder of deliverables (markdown + interactive HTML + PDF). Advisors are
  *real people* whose judgment the user admires. Best for high-stakes decisions you'll revisit
  and share.

If the user clearly wants named real-world advisors, persisted config, or shareable artifacts,
redirect them to boardroom.

## How It Runs

Run all three stages without stopping to interview the user. The whole appeal is that it just
works from the question alone. The only acceptable pause is if the question is too vague to
answer at all — in that case ask one tight clarifying question, then proceed.

### Choosing the Council (do this first, silently)

Pick **4–6 advisors**, each a distinct thinking lens. Default to these five unless the question
calls for something better:

1. **The Contrarian** — only looks for how this fails. Assumes the plan is wrong and tries to
   prove it.
2. **The First-Principles Thinker** — rips apart every assumption and rebuilds from the ground
   up. Refuses to accept framing for granted.
3. **The Expansionist** — hunts for the upside being left on the table. Asks "what if this is
   thought too small?"
4. **The Outsider** — knows nothing about the user's industry and isn't impressed by its norms.
   Asks the naive question that insiders stopped asking.
5. **The Executor** — cares only about what you'll actually do Monday morning. Allergic to
   theory; wants the concrete next move.

Adapt when the question warrants it. A technical architecture question might swap the Outsider
for a **Reliability Engineer**; a personal decision might add a **Long-Term Self** lens. If the
user named specific lenses or advisors in their request, use those. Keep the set diverse — the
council is worthless if the advisors think alike.

State the roster in one line before you begin (e.g., "Convening 5 advisors: Contrarian,
First-Principles, Expansionist, Outsider, Executor"), so the user knows who's in the room.

### Stage 1 — First Opinions (parallel subagents)

Spin up **one agent per advisor, all in parallel**, in a single message. Each agent answers the
question independently and has no knowledge of the others — this independence is what makes the
later peer review meaningful.

Instruct each agent:

```
You are an advisor on a council, answering a question through one specific lens.

Your lens: [Name] — [one-sentence description of how this lens thinks and what it cares about]

The question before the council is:
[question + any context the user provided]

Answer the question fully, but ONLY through your lens. Don't try to be balanced or cover every
angle — that's other advisors' job. Be the sharpest possible version of YOUR perspective.

- Lead with your actual answer/recommendation, then justify it.
- Be concrete and specific. Use numbers, examples, or mechanisms where they help.
- Name the single thing you think everyone else will get wrong.
- 250–500 words. No preamble.
```

Collect all answers. If an agent fails, proceed with the ones that succeeded (a council of 3
still works).

### Stage 2 — Peer Review (inline, anonymized)

Now you (the main session) run the review inline. Strip every advisor's name and relabel the
answers **Response A, Response B, Response C, …** in random order. The reviewers must not know
which lens wrote which answer — blind review is the whole point.

For **each advisor lens**, write a short critique of every response and produce a ranking.
Review from that lens's worldview — the Contrarian ranks differently than the Executor. For
each reviewer, output:

- 1–2 sentences per response on what it does well and poorly.
- A ranking line in exactly this format (mirrors Karpathy's council):

```
FINAL RANKING: 1. Response X  2. Response Y  3. Response Z  ...
```

Then compute an **aggregate ranking** by averaging each response's position across all
reviewers (lower average = stronger). Note where the council strongly agreed and where it
split — disagreement is signal, not noise.

Keep this stage tight and scannable. It's the reasoning, not the deliverable.

### Stage 3 — Chairman Synthesis (inline)

Step into the role of Chairman and synthesize everything into the final answer. You have all
the original opinions, the blind critiques, and the aggregate ranking. Do not just pick the
top-ranked answer — synthesize across the council, keeping the strongest reasoning and
discarding what the peer review exposed as weak.

Produce the final output for the user:

> ## Council Verdict: [question, condensed]
>
> **The call:** [the clear recommendation, 1–3 sentences. Take a position — hedging defeats
> the purpose.]
>
> **Why:** [2–4 bullets of the reasoning that survived peer review, attributed to lenses where
> useful — e.g. "The Contrarian's point about X held up; the Expansionist's upside case did not."]
>
> **What the council split on:** [the genuine disagreement, and how you resolved it — or that
> it's a real judgment call the user must make, with the tradeoff named.]
>
> **Monday morning:** [2–4 concrete next steps the user can act on immediately. This is the
> Executor's contribution — make it actionable, not aspirational.]
>
> **Strongest single point:** [the one insight from the whole session most worth remembering.]

After presenting, offer to save a record:

> Want me to save the full council transcript (all opinions + review + verdict) to
> `council-[slug].md`?

Only write the file if the user says yes. If they do, save the full three-stage record —
roster, every first opinion, the anonymized critiques and aggregate ranking, and the verdict —
to `council-[slug].md` in the current directory, where `[slug]` is a short kebab-case version
of the question.

## Notes

- **Keep it fast.** The contract with the user is a quick, sharp, multi-angle read — not a
  research project. If the question is large, the council gives a strong directional answer and
  flags what would need deeper work, rather than trying to be exhaustive.
- **Diversity over headcount.** Five genuinely different lenses beat eight overlapping ones.
- **The verdict must take a position.** A council that concludes "it depends" has failed. Name
  the call, then name the conditions under which you'd change it.
- **Faithful to the source.** The three stages — independent opinions → blind ranked peer
  review → chairman synthesis — come directly from Karpathy's LLM Council. The adaptation is
  using lenses-within-Claude rather than multiple external models.
