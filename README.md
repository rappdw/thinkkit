# Thinkkit

Thinking tools for AI — a Claude Code plugin that combines structured exploration, strategic debate, CISO review, discovery scaffolding, and codebase mapping into a single installable package.

## Installation

### As a marketplace (recommended)

Thinkkit is both a plugin and a marketplace. Add it directly:

```
/plugin marketplace add https://github.com/rappdw/thinkkit
/plugin install thinkkit
```

### Via local directory (for development)

```bash
claude --plugin-dir /path/to/thinkkit
```

## Skills

### Thinking Tools

| Skill | Command | Use when... |
|-------|---------|-------------|
| **Boardroom** | `/thinkkit:boardroom` | You want to pressure-test a decision by having AI-simulated advisors debate it — a "Monte Carlo simulation with intelligence" |
| **CISO Review** | `/thinkkit:ciso-review` | You need to evaluate a vendor, product, or your own approach through a skeptical CISO's eyes |
| **Explore With Me** | `/thinkkit:explore-with-me` | You need to think through a problem, explore a topic in depth, or structure your thinking on any open-ended question |
| **Init Discovery** | `/thinkkit:init-discovery` | You're starting a multi-session investigation and need a structured project scaffold |
| **Map The Repo** | `/thinkkit:map-the-repo` | You want to document a codebase, generate a browsable wiki, or onboard someone to a project |
| **Create Spec** | `/thinkkit:create-spec` | You need a single specification document complete enough to reconstruct a repo from scratch |
| **Take Notes** | `/thinkkit:take-notes` | You're in a meeting and want to feed terse observations that get expanded into structured notes |
| **Resolve Against Transcript** | `/thinkkit:resolve-against-transcript` | You have a meeting transcript and notes, and want to find and fix discrepancies between them |

## Production Tools

Looking for document conversion (Markdown to PDF, DOCX, HTML, email)? See [synthkit](https://github.com/rappdw/synthkit) — installable via `pip install synthkit` or `uvx synthkit`.

## Attribution

The boardroom skill is inspired by [Allie K Miller](https://x.com/alliekmiller).

## License

MIT
