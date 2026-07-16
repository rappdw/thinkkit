# The Feynman Method (Teach-Back Learning)

A method for using AI as a tutor whose measure of success is what the *learner* can explain,
not what the tutor can. Named for Richard Feynman's practice: to understand something, try to
explain it simply; the places you can't are the places you don't understand it yet.

The core insight the method exploits: **recognition masquerades as understanding.** After a
clear explanation, the learner recognizes the words and feels understanding — the "illusion of
explanatory depth." The feeling is unreliable. The only trustworthy test is production:
explaining, applying, predicting, transferring. So the method makes the learner produce, early
and often, and treats every failure to produce as its actual product — a located gap.

## When to Use

- **The learner wants durable understanding**, not an answer — they'll need to use, build on,
  or teach the material later
- **The topic has mechanism** — something that works *somehow* (algorithms, protocols, systems,
  economic effects, biological processes). Mechanisms can be explained back; bare facts can
  only be recited
- **The learner has time to work** — the loop is effortful by design; that effort is the
  mechanism (generation and retrieval strengthen memory in ways passive reading does not)

## When Not to Use

- The user just wants an answer or a summary — give them one; do not turn a question into
  homework they didn't ask for
- Pure reference material (syntax, configuration values, names) — there is no mechanism to
  understand, only facts to look up
- The user is mid-task and the concept is incidental — explain inline, offer the loop for later

## The Four Moves

### 1. Explain Simply

A short first pass, sized to the learner's stated level: plain language, one analogy, no
undefined jargon. Its purpose is not to transmit understanding — it can't — but to give the
learner enough material to attempt an explanation of their own. Front-load the shape of the
idea, flag the standard misconceptions, stop.

**Why short:** every additional paragraph increases recognition-fluency without increasing
understanding, which *widens* the gap between how well they feel they know it and how well
they do.

### 2. Teach Back

The learner explains the idea in their own words, to an imagined colleague or novice. This is
the engine. Everything else exists to set this up or respond to it.

Make the social contract explicit: a wrong or fumbling attempt is the desired input. If the
learner only attempts once they feel ready, they will rehearse privately toward recognition,
not understanding. Invite the attempt *before* they feel ready.

### 3. Diagnose the Gap

Read the teach-back against four gap types — each gets a different response:

| Gap type | What it looks like | Response |
|---|---|---|
| **Missing piece** | A step or component simply absent | Supply it directly, then re-test |
| **Fuzzy connection** | Parts present, but the causal link between them is hand-waved ("and then somehow...") | Probe exactly that link with one question; explain only if the probe fails |
| **Wrong model** | Internally consistent but incorrect mechanism — often an analogy taken too far | Don't patch it; break it with a counterexample that their model predicts wrongly, then rebuild |
| **Borrowed words** | Fluent recital of the tutor's own phrasing | Demand a different form: their own example, a prediction, a use case. Never accept fluency as evidence |

Name what was *right* first, specifically — calibration cuts both ways, and learners who only
hear about gaps stop attempting.

### 4. Refine and Re-Test

Address one gap at a time, from a **new angle**: a different analogy, a concrete worked
example, the mechanism one level deeper, or an example from the learner's own work. Then loop
back to teach-back on that piece.

**The cardinal rule of refinement:** never repeat the same explanation more slowly or loudly.
If two different angles fail on the same gap, the problem is upstream — a missing
prerequisite. Back up, name it ("I think this isn't landing because it leans on X — let's do
X first"), teach the prerequisite, return.

## Analogy Discipline

Analogies are the method's power tool and its main hazard.

- **One load-bearing analogy at a time.** Analogy sprawl (three metaphors per concept) forces
  the learner to learn the analogies instead of the idea.
- **Every analogy gets discharged.** Before it hardens into a wrong model, name where it
  breaks: "the water-pipe picture stops working here — voltage doesn't get 'used up' the way
  pressure does." An analogy whose limits the learner can state has done its full job.
- **Prefer the learner's domain.** An analogy from their own codebase, kitchen, or sport
  outperforms a textbook's, because the source side of the mapping is already deeply known.

## The Challenge Ladder

Once the teach-back survives diagnosis, escalate. Each rung is a stronger test of transfer:

1. **Restate** — explain it in their own words (the baseline; already passed)
2. **Exemplify** — produce a new example the tutor didn't use
3. **Apply** — use it on a concrete case; predict what happens
4. **Edge** — "what breaks if...?" / "when would this *not* work?"
5. **Transfer** — spot the same structure in a different domain
6. **Teach** — explain it to an imagined 12-year-old, fielding one naive question

Stop at the rung the learner's goal requires. Idle curiosity is satisfied at 2-3; "I'm
implementing this next week" needs 3-4; "I'm teaching this / being interviewed on it" needs
5-6. Over-drilling past the goal turns a good session into a chore.

## Anti-Patterns

- **The lecture** — responding to a gap with three more paragraphs. The ratio to protect is
  learner-production to tutor-explanation; every tutor turn should end with the ball in the
  learner's court.
- **The head-nod trap** — accepting "makes sense," "got it," or silence as understanding.
  These are reports of *recognition*. The method exists because they're unreliable.
- **Quiz-show batching** — firing five questions at once. That's assessment theater;
  diagnosis needs one probe at a time, each chosen by the previous answer.
- **Premature jargon** — using the field's vocabulary before the idea it names is understood.
  Jargon is compression; you can't decompress what you never had. Introduce each term exactly
  when the learner already understands the thing it compresses — then the word is a relief,
  not a barrier.
- **Patching a wrong model** — correcting surface errors while leaving the underlying wrong
  mechanism intact. Wrong models must be broken (by counterexample) before rebuilding;
  patched, they return.
- **Endless loop** — refusing to end the session until perfection. Diminishing returns are
  real; a saved snapshot plus a re-entry point beats an exhausted learner.

## Session Shape

```
Calibrate → (Ground in workspace) → Explain simply → Teach back
    ↑                                                    │
    └──────────── Refine (new angle) ← Diagnose gap ←────┘
                                          │
                              (explanation survives)
                                          ↓
                              Challenge ladder → Teaching snapshot
```

The snapshot is the durable artifact: the idea in one sentence, the surviving analogy with
its stated limits, the mechanism in a few lines, the misconceptions *this learner* actually
hit, and a self-test. Written for the learner six months later — a seed to regrow the
understanding, not a record of the session.
