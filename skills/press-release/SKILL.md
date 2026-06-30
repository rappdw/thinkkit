---
name: press-release
user-invocable: true
argument-hint: [what you're announcing]
allowed-tools: Read, Write, WebSearch, WebFetch
description: >
  Draft a complete, reporter-ready press release from a short description of what you're
  announcing. Use this skill whenever the user wants to write, draft, or generate a press
  release, announcement, or "PR" for a product launch, customer win, funding round, partnership,
  program, or milestone. Trigger on phrases like "press release", "draft a PR", "write an
  announcement", "we're announcing X", "write a release for our launch", "announce our
  partnership with Y", or "/thinkkit:press-release". The skill extracts what it can from the
  prompt, asks only for the essentials it's still missing, then writes the release in a proven
  six-section structure. Lean toward triggering — if the user is clearly trying to produce
  announcement copy, use this skill.
---

# Press Release

Turn a short description of an announcement into a polished, reporter-ready press release. The
skill is **prompt-first**: pull everything possible from what the user already gave you, ask
only for the essentials still missing, then write the release in a fixed six-section structure
that's built to get an article written.

Two reference files define the method — read them before drafting:
- [references/worksheet.md](references/worksheet.md) — the intake checklist (what inputs a
  strong release needs). Use it to figure out what's *missing*, not as an interrogation script.
- [references/template.md](references/template.md) — the six-section output structure with a
  worked example for each section. The release you write must follow this structure.

## Workflow

### 1. Mine the prompt first

Read the user's request (and any files or context they pointed you at) and extract as many
worksheet inputs as you can. Most announcements already contain the fact, the company, and the
gist of why it matters. Do **not** ask for anything you can reasonably infer or already have.

### 2. Ask only for the missing essentials

A credible release needs these. If any are genuinely missing after step 1, ask for them — all
at once, in a single grouped batch, not one at a time:

- **The fact** — what, specifically, is being announced.
- **The company** — name plus one line on what it does.
- **The one takeaway** — the single thing a reader should come away understanding.
- **Up to 3 key messages** — why the news matters, how a customer benefits, how it's different.
- **An external quote source** — ideally a customer, else an analyst/industry expert (name +
  title). If none is available, say so and the release will note the quote as a placeholder.
- **A company spokesperson** — name + title for the internal quote.
- **Availability / pricing** — when people can get it, and through what channel.
- **Target audience** — trade press, vertical press, business press, etc. (shapes tone).

Everything else on the worksheet (PR goals, support points, third-party contacts) is a bonus —
fold it in if provided, but don't block on it.

### 3. Gather supporting stats (optional)

The factoid paragraph (section 2) is stronger with objective third-party numbers a reporter can
cite. If the user didn't supply stats, you may use WebSearch to find relevant industry figures
and footnote their sources.

**Never fabricate a number or a citation.** Any stat you haven't verified against a real source
must be written as `[VERIFY: what to confirm / candidate source]` so the user knows to check it
before publishing.

### 4. Write the release

Draft all six sections per [references/template.md](references/template.md):

1. **Opener** (~3 sentences: the news, what's new, the implication for readers)
2. **Factoid paragraph** (third-party stats → customer-impact punchline)
3. **External quote** (customer or analyst — not a company employee)
4. **Product details & facts** (plain language → tie back to customer value)
5. **Company quote** (spokesperson reiterating function and value)
6. **Availability & more info**

Discipline while drafting:
- Keep the opener tight — three sentences if you can.
- Write in plain language; assume the reporter isn't an expert in the user's domain.
- Lead a proposed headline/subhead above the body.
- Mark every inference with `[ASSUMPTION: ...]` and every real gap with `[NEEDS INPUT: ...]`
  inline, so the user can see exactly what to confirm or fill.

### 5. Save and offer conversions

Save the release to `press-release-<slug>.md` in the current directory (slug = short
kebab-case of the announcement), and show it inline. Then offer formats:

> Saved to `press-release-<slug>.md`. Want me to convert it for sharing? I can produce a PDF
> (`md2pdf`), a Word doc (`md2doc`), or styled HTML (`md2html`).

Only run a conversion if the user asks.

## Notes

- **Prompt-first is the contract.** The appeal is that a one-line announcement can become a full
  draft with minimal back-and-forth. Resist turning this into a full worksheet interview — ask
  for essentials only.
- **A draft is the goal, not final copy.** It's normal and good to hand back a release peppered
  with `[ASSUMPTION]`/`[NEEDS INPUT]`/`[VERIFY]` markers — they tell the user precisely what to
  finish. A clean-looking release built on invented facts is worse than an honest one with gaps.
- **The structure is fixed; the content is generic.** The six-section shape is the method. It
  works for any company and any kind of announcement — product, customer win, funding,
  partnership, program, milestone.
