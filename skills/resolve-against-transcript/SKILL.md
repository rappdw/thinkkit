---
name: resolve-against-transcript
description: >
  Post-meeting reconciliation tool. Compares a meeting transcript against
  meeting notes to find discrepancies (missing content, attribution errors,
  mischaracterizations, missing action items) and walks through resolving each
  one interactively. Use this skill whenever the user wants to "resolve notes
  against a transcript", "check my meeting notes against the recording",
  "verify meeting notes", "reconcile notes with transcript", or has both a
  transcript and notes file and wants to ensure accuracy. Also trigger when
  the user mentions checking `[unverified]` tags or validating speaker
  attribution against a transcript.
user-invocable: true
argument-hint: "<transcript-file> [notes-file]"
allowed-tools: Read, Write, Glob
---

# Resolve Against Transcript

Compare a meeting transcript against meeting notes and interactively resolve
every discrepancy. The transcript is the source of truth; the notes are what
get corrected.

## Why this exists

Meeting notes taken in real time (whether by `/take-notes` or by hand) are
fast but imperfect. Speakers get misattributed, points get paraphrased in
ways that shift meaning, action items slip through. This skill treats the
transcript as ground truth and systematically surfaces every place where the
notes diverge from what was actually said.

## Invocation

Accept two arguments:
1. A transcript file path (.txt, .md, .vtt, .srt, or similar)
2. A meeting notes file path (typically from `meeting-notes/`)

**If either is missing**, prompt for it. If only one file is provided and a
`meeting-notes/` directory exists, attempt to match by date or title slug.
For example, if the transcript is named `2025-03-28-api-review.vtt`, look
for `meeting-notes/2025-03-28-api-review.md` or similar.

## Step 1: Read and understand both files

Read the transcript and the notes file in full. Before flagging anything,
build a mental model of:
- Who the attendees are and their roles
- The topics discussed and their sequence
- Decisions made and action items assigned
- The overall arc of the meeting

This context prevents false positives. A note that summarizes three transcript
exchanges into one sentence isn't a discrepancy; it's reasonable compression.
A note that changes who said what, or omits a decision, is a real problem.

## Step 2: Identify discrepancies

Scan for these categories, roughly in order of significance:

### Factual discrepancies
Statements in the notes that contradict what was actually said. These are the
most serious because they create a false record.

### Mischaracterizations
Points that were expanded or paraphrased in the notes in a way that shifts
meaning from the original. The note says something subtly different from what
the speaker actually meant.

### Attribution errors
Speaker mismatches. Pay special attention to anything marked `[unverified]`
in the notes. Check each one against the transcript.

### Missing content
Topics, decisions, or significant points present in the transcript but absent
from the notes. Not every transcript utterance needs a note; focus on things
that matter: decisions, commitments, technical details, disagreements.

### Missing action items
Commitments or follow-ups mentioned in the transcript ("I'll send that over
by Friday", "let's circle back on the auth flow next week") that aren't
captured in the Action Items section of the notes.

## Step 3: Interactive resolution

Present discrepancies one at a time, ordered by significance (factual errors
first, missing content last). For each one, use this format:

---

**Discrepancy N of M** | Category

**Transcript excerpt:**
> Verbatim quote from the transcript

**Notes (current):**
> The corresponding section from the notes, or "[not present]" if missing

**Issue:** Clear, one-sentence statement of what's wrong.

**Proposed resolution:**
> The specific updated text, new entry, or corrected attribution.

Accept, modify, or skip?

---

When the user accepts, apply the change to the notes file immediately. When
they modify, apply their version. When they skip, move on and note it for
the summary.

Keep the conversation focused. Don't editorialize about why a discrepancy
might have happened or offer commentary on the meeting content. Show the
problem, propose the fix, wait for the decision.

## Step 4: Verification cleanup

After all discrepancies are resolved, sweep the notes for any remaining
`[unverified]` tags:

- If the transcript confirms the attribution, remove the tag silently
  (or propose the removal if you want to be safe)
- If the transcript contradicts the attribution, propose the correction
  with the transcript evidence
- If the transcript is ambiguous (speaker not clearly identifiable), leave
  the tag and add a brief note explaining why it couldn't be resolved

## Step 5: Summary

After resolution is complete, output a brief summary:

```
## Resolution Summary
- Discrepancies found: N
- Resolved: N
- Skipped: N
- [unverified] tags resolved: N
- [unverified] tags remaining: N (with reasons)
```

## Transcript format handling

Transcripts come in various formats. Handle at least:

- **Plain text / Markdown**: Speaker names typically appear as "Speaker:" or
  "**Speaker**:" at the start of lines
- **VTT / SRT**: Timestamped subtitle format with optional speaker labels.
  Parse timestamps but don't include them in the output unless relevant
  to a discrepancy
- **Raw transcription**: May lack speaker labels entirely. Do your best to
  infer speakers from context, but flag low-confidence attributions

## Writing style for proposed resolutions

Match the voice and style of the existing notes. If the notes are terse and
direct, keep resolutions terse and direct. If they use a specific format for
action items or speaker attribution, follow that format exactly.

- No em-dashes
- Quote transcript excerpts verbatim
- Direct and concise; show the problem, propose the fix
- When adding new content to the notes, place it in the correct chronological
  position, not just appended at the end
