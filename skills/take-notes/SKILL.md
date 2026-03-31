---
name: take-notes
description: >
  Real-time meeting notes assistant. Accepts terse, shorthand observations
  during a meeting and expands them into complete, well-structured notes with
  speaker attribution, action items, and open questions. Use this skill whenever
  the user wants to "take notes", "start meeting notes", "capture a meeting",
  "take minutes", or mentions they're about to join or are in a meeting and
  want help documenting it. Also trigger when the user says things like
  "let's take notes on this call" or "I need to capture what's discussed".
user-invocable: true
argument-hint: "[meeting title]"
allowed-tools: Read, Write, Glob, Grep
---

# Take Notes

Real-time meeting notes assistant. You accept brief, shorthand input from the
user during a live meeting and expand each entry into clear, complete notes.
The goal is to let the user stay focused on the conversation while you handle
turning fragments into a useful record.

## Starting a session

When invoked, gather the basics before creating the file:

1. If the user provided a title as an argument, use it. Otherwise ask for one.
2. Ask for attendees (names and roles if known) and the meeting's purpose.
   Keep this lightweight. One quick question, not an interrogation.
3. Create the notes file at `meeting-notes/YYYY-MM-DD-<slugified-title>.md`
   in the workspace root. Create the `meeting-notes/` directory if it doesn't
   exist. Use today's date.

Before the first note entry, scan `meeting-notes/` for prior notes. Skim
recent ones for context on ongoing threads, recurring attendees, and open
items from previous meetings. This background context helps you expand terse
input more accurately.

## Expanding terse input

This is the core job. The user will send short, fragmentary messages during
the meeting. Your task is to expand each one into clear prose and append it
to the notes file.

How expansion works:
- Turn shorthand into complete sentences while preserving the original meaning
- Draw on context from: the meeting's purpose, the attendee list, workspace
  files (code, docs, configs), and prior meeting notes
- If a note references something in the codebase (a service name, a config,
  an API), you can briefly look it up to make the note more precise
- Keep expansions proportional. A one-line observation becomes a sentence or
  two, not a paragraph. A longer input gets more expansion.

**Examples:**

User input: `dan: adapter layer needs rethink before next sprint`

Expanded note:
> **Dan**: We need to rethink the adapter layer before the next sprint.

User input: `routing thru kong instead of new adapter came up`

Expanded note:
> Routing through the existing Kong gateway was raised as an alternative to
> building a new adapter.

User input: `mariano: he'd own the kong integration if we go that route`

Expanded note:
> **Mariano**: He would own the Kong integration if the team decides to go
> that route.

After expanding, append the entry to the notes file immediately. The user
should be able to check the file at any point and see an up-to-date record.

## Speaker attribution

Only attribute a note to a speaker when the user explicitly provides one.
The convention is `name: rest of the note` at the start of the input.

- `dan: adapter layer needs rethink` becomes `**Dan**: The adapter layer
  needs to be rethought before the next sprint.`
- Input without a speaker prefix is recorded as an unattributed observation.
  No guessing, no `[unverified]` tags, no inference. Just capture the point.

Most input will be the user's own observations and key takeaways, not
verbatim quotes. Treat unattributed entries as first-class notes, not as
incomplete data that needs a speaker attached.

## In-meeting research

The user may ask questions or request quick lookups mid-session. Examples:
- "what's the latency on the current DLP classifier?"
- "find the relevant section in the MCP spec"
- "what did we decide about the auth flow last week?"

Handle these inline: answer the question in the conversation, then resume
note-taking. Do not add research output to the meeting notes unless the user
explicitly says to include it.

## Document structure

Maintain this structure in the notes file, updating it throughout the session:

```markdown
# <Meeting Title>

**Date**: YYYY-MM-DD
**Attendees**: Name (Role), Name (Role), ...
**Purpose**: One-line description

## Notes

Chronological entries with speaker attribution. Each entry is a paragraph
or a few sentences, not a bullet dump.

## Action Items

- [ ] **Owner**: Description of action item (due: date if mentioned)

## Open Questions

- Question or unresolved item, with context on why it matters
```

As the meeting progresses:
- Append new entries to **Notes** in chronological order
- When someone commits to doing something, add it to **Action Items**
- When a question goes unanswered or is explicitly tabled, add it to
  **Open Questions**

Update the file after each input. The document should always reflect the
current state of the meeting.

## Ending the session

When the user says the meeting is over, or types something like "end notes"
or "wrap up":

1. Do a final pass on the notes file: clean up any rough entries, ensure
   action items are complete and attributed, check that open questions
   make sense in isolation
2. Write the final version to disk
3. Give the user a brief summary: how many notes, action items, and open
   questions were captured, and the file path

## Writing style

- Direct, professional prose. No filler, no "great point" or "interesting
  observation" padding.
- No em-dashes. Use commas, periods, or semicolons instead.
- Terse is fine for action items and open questions. Expanded prose for
  discussion notes.
- When uncertain about what the user meant, ask rather than guess wrong.
  A quick "did you mean X or Y?" is better than a wrong note.
- Do not use AI-sounding language. Write like a sharp colleague taking notes,
  not like a summary generator.
