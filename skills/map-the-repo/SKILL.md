---
name: map-the-repo
user-invocable: true
argument-hint: [path to repo]
allowed-tools: Bash, Read, Write, Glob, Grep, Agent
description: >
  Generate comprehensive documentation and a browsable wiki for any codebase. Use this skill
  whenever the user wants to document a repo, generate a wiki, understand architecture, produce
  onboarding docs, map dependencies, or says things like "document this repo", "explain this
  codebase", "map the repo", "generate a wiki", "architecture docs", "I need to understand
  this project", or "onboard me". Also useful when handing off a repo to a new engineer or
  agent. This is the documentation companion to /thinkkit:explore-with-me — explore first to understand,
  then map to document.
---

# Map the Repo

Generate a browsable wiki from a codebase. The script produces structural scaffolding; your
job is to enrich it with genuine architectural insight.

## Workflow

### 1. Orient

Before running the script, build context:

- Check for existing discovery output (init-discovery CLAUDE.md, explore-with-me findings)
  and use it to inform your understanding
- Read `README.md`, `pyproject.toml` / `package.json` / `go.mod` / `Cargo.toml` to identify
  the language, framework, and project type
- Scan the top-level directory structure to understand the layout

### 2. Check LSP Setup

After identifying the project's languages, check whether the corresponding LSP plugins and
language server binaries are installed. This dramatically improves enrichment quality —
especially for non-Python languages where the script falls back to regex.

**Language server requirements by language:**

| Language | Binary | Install | Plugin |
|----------|--------|---------|--------|
| Python | `pyright-langserver` | `pip install pyright` | `pyright-lsp` |
| TypeScript/JS | `typescript-language-server` | `npm install -g typescript-language-server typescript` | `typescript-lsp` |
| Go | `gopls` | `go install golang.org/x/tools/gopls@latest` | `gopls-lsp` |
| Rust | `rust-analyzer` | See [rust-analyzer.github.io](https://rust-analyzer.github.io) | `rust-analyzer-lsp` |
| Java | `jdtls` | See [eclipse.org/jdtls](https://projects.eclipse.org/projects/eclipse.jdt.ls) | `jdtls-lsp` |
| C/C++ | `clangd` | `apt install clangd` / `brew install llvm` | `clangd-lsp` |
| Kotlin | `kotlin-language-server` | See [github.com/fwcd/kotlin-language-server](https://github.com/fwcd/kotlin-language-server) | `kotlin-lsp` |
| Swift | `sourcekit-lsp` | Bundled with Xcode / Swift toolchain | `swift-lsp` |
| PHP | `intelephense` | `npm install -g intelephense` | `php-lsp` |
| Lua | `lua-language-server` | See [github.com/LuaLS/lua-language-server](https://github.com/LuaLS/lua-language-server) | `lua-lsp` |
| C# | `csharp-ls` | `dotnet tool install -g csharp-ls` | `csharp-lsp` |

**Check procedure** — for each primary language detected in the repo:

1. Check if the binary is on PATH:
   ```bash
   which pyright-langserver 2>/dev/null  # example for Python
   ```

2. If the binary is missing, offer to install it:
   > I noticed this is a Python project but `pyright` isn't installed. LSP support
   > gives me much better type information and cross-file analysis for enriching the docs.
   > Want me to install it? (`pip install pyright`)

3. Check if the Claude Code LSP plugin is installed by running `/plugin` commands. If the
   binary is present but the plugin isn't, tell the user:
   > `pyright` is installed but the Claude Code LSP plugin isn't. Run:
   > `/plugin install pyright-lsp`
   > Then we can continue with full code intelligence.

4. If the user declines or installation isn't possible, proceed without LSP — the script's
   AST/regex analysis plus manual code reading still produces good results.

Only check languages that are actually present in the repo. Don't suggest installing Go
tooling for a Python-only project.

### 3. Run the Script

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/map-the-repo/scripts/map.py --repo-path . --output-path ./wiki
```

The script generates:
- `wiki/docs/*.md` — Markdown documentation (index, architecture, data flows, API reference,
  glossary, per-module docs)
- `wiki/site/index.html` — Self-contained browsable site (dark theme, search, Mermaid diagrams)

### 4. Enrich

This is the critical step. The script produces structure — file listings, function signatures,
import graphs. You provide understanding.

If LSP was set up in step 2, use go-to-definition, find-references, and call hierarchies
freely as you work — they give you accurate type information and cross-file relationships
that the script's static analysis may have missed.

Read every generated file in `wiki/docs/` and rewrite weak sections:

- **`architecture.md`** — The Mermaid diagram should immediately convey system shape. Add
  prose explaining *why* the system is structured this way, not just *what* the structure is.
  Note key design decisions and their tradeoffs.

- **`data-flows.md`** — Add sequence diagrams for the 2-3 most important flows through the
  system. Explain what triggers each flow and what the end state is.

- **Module docs** (`modules/*.md`) — Each should read like a senior engineer wrote it after
  a day in the code. Explain the module's role in the system, its key abstractions, and any
  non-obvious behavior. Don't just list functions — explain what problems they solve.

- **`glossary.md`** — Add domain-specific terms that a new engineer would need to understand.
  Define them in the context of this specific codebase, not generic definitions.

- **`api-reference.md`** — Verify signatures are correct. Add usage examples for the most
  important public APIs.

After enriching the markdown files, regenerate the HTML site to pick up your changes:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/map-the-repo/scripts/map.py --repo-path . --output-path ./wiki --rebuild-site
```

### 5. Present

Tell the user:
- Where to open the site (`wiki/site/index.html`)
- What was found (number of modules, public APIs, key architectural patterns)
- Any areas where the documentation is thin and could use human input
