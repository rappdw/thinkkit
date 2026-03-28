#!/usr/bin/env python3
"""Generate a browsable wiki from a code repository.

Usage:
    python map.py [--repo-path PATH] [--output-path PATH] [--rebuild-site]

Produces:
    wiki/docs/*.md          Markdown documentation
    wiki/site/index.html    Self-contained browsable site
"""

import argparse
import ast
import json
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "dist", "build", "venv", ".venv",
    ".claude", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".eggs", ".nox", "htmlcov", ".coverage", "wiki",
}

SKIP_SUFFIXES = {".pyc", ".pyo", ".so", ".dylib", ".lock", ".min.js", ".min.css"}

LANGUAGE_MAP = {
    ".py": "Python", ".pyi": "Python",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript",
    ".go": "Go",
    ".java": "Java",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".c": "C", ".h": "C/C++", ".hpp": "C++",
    ".swift": "Swift",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".scala": "Scala",
    ".ex": "Elixir", ".exs": "Elixir",
    ".sh": "Shell", ".bash": "Shell",
}

CONFIG_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "tsconfig.json",
    "go.mod", "go.sum",
    "Cargo.toml",
    "Gemfile", "Rakefile",
    "Makefile", "CMakeLists.txt",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github", ".gitlab-ci.yml",
}

# ── Data Classes ───────────────────────────────────────────────────────────────


@dataclass
class FunctionInfo:
    name: str
    signature: str
    docstring: str = ""
    decorators: list[str] = field(default_factory=list)
    line: int = 0
    is_public: bool = True


@dataclass
class ClassInfo:
    name: str
    bases: list[str] = field(default_factory=list)
    docstring: str = ""
    methods: list[FunctionInfo] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    line: int = 0
    is_public: bool = True


@dataclass
class FileInfo:
    path: Path
    relative: str
    language: str
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    docstring: str = ""
    lines: int = 0


@dataclass
class ModuleInfo:
    name: str
    path: str
    files: list[FileInfo] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return sum(f.lines for f in self.files)

    @property
    def primary_language(self) -> str:
        lang_counts: dict[str, int] = {}
        for f in self.files:
            lang_counts[f.language] = lang_counts.get(f.language, 0) + 1
        return max(lang_counts, key=lang_counts.get) if lang_counts else "Unknown"


@dataclass
class RepoMap:
    name: str
    root: Path
    modules: list[ModuleInfo] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    total_lines: int = 0
    config_files: list[str] = field(default_factory=list)


# ── Discovery ──────────────────────────────────────────────────────────────────


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS or part.startswith("."):
            return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def _detect_project_name(repo_path: Path) -> str:
    """Try to detect the real project name from config files."""
    # pyproject.toml
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8")
            m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1)
        except Exception:
            pass
    # package.json
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "name" in data:
                return data["name"].split("/")[-1]  # strip scope
        except Exception:
            pass
    # Cargo.toml
    cargo = repo_path / "Cargo.toml"
    if cargo.exists():
        try:
            text = cargo.read_text(encoding="utf-8")
            m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1)
        except Exception:
            pass
    # go.mod
    gomod = repo_path / "go.mod"
    if gomod.exists():
        try:
            text = gomod.read_text(encoding="utf-8")
            m = re.search(r'^module\s+(\S+)', text, re.MULTILINE)
            if m:
                return m.group(1).split("/")[-1]
        except Exception:
            pass
    return repo_path.resolve().name


def discover_repo(repo_path: Path) -> RepoMap:
    print(f"Scanning {repo_path.resolve()}...")
    project_name = _detect_project_name(repo_path)
    repo = RepoMap(name=project_name, root=repo_path.resolve())
    modules_map: dict[str, ModuleInfo] = {}

    # Collect config files
    for item in sorted(repo_path.iterdir()):
        if item.name in CONFIG_FILES:
            repo.config_files.append(item.name)

    # Walk all code files
    for path in sorted(repo_path.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_path)
        if should_skip(rel):
            continue
        ext = path.suffix.lower()
        if ext not in LANGUAGE_MAP:
            continue

        relative = str(rel)
        language = LANGUAGE_MAP[ext]
        parts = rel.parts

        # Determine module grouping
        if parts[0] == "src" and len(parts) > 2:
            module_name = parts[1]
            module_path = f"src/{parts[1]}"
        elif len(parts) > 1:
            module_name = parts[0]
            module_path = parts[0]
        else:
            module_name = "(root)"
            module_path = "."

        # Analyze
        try:
            if language == "Python":
                fi = analyze_python(path, relative)
            else:
                fi = analyze_other(path, relative, language)
        except Exception as e:
            print(f"  Warning: could not analyze {relative}: {e}")
            fi = FileInfo(path=path, relative=relative, language=language)

        if module_name not in modules_map:
            modules_map[module_name] = ModuleInfo(name=module_name, path=module_path)
        modules_map[module_name].files.append(fi)

    repo.modules = sorted(modules_map.values(), key=lambda m: m.name)

    # Tally stats
    for mod in repo.modules:
        for fi in mod.files:
            repo.languages[fi.language] = repo.languages.get(fi.language, 0) + 1
            repo.total_files += 1
            repo.total_lines += fi.lines

    print(f"  Found {repo.total_files} code files across {len(repo.modules)} modules")
    print(f"  Languages: {', '.join(f'{lang} ({n})' for lang, n in sorted(repo.languages.items(), key=lambda x: -x[1]))}")
    return repo


# ── Python AST Analysis ───────────────────────────────────────────────────────


def _get_decorator_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return ast.unparse(node)
    if isinstance(node, ast.Call):
        return _get_decorator_name(node.func)
    return ast.unparse(node)


def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    num_args = len(node.args.args)
    num_defaults = len(node.args.defaults)
    defaults_offset = num_args - num_defaults

    for i, arg in enumerate(node.args.args):
        parts = [arg.arg]
        if arg.annotation:
            try:
                parts.append(f": {ast.unparse(arg.annotation)}")
            except Exception:
                pass
        default_idx = i - defaults_offset
        if default_idx >= 0:
            try:
                parts.append(f" = {ast.unparse(node.args.defaults[default_idx])}")
            except Exception:
                parts.append(" = ...")
        args.append("".join(parts))

    if node.args.vararg:
        a = f"*{node.args.vararg.arg}"
        if node.args.vararg.annotation:
            try:
                a += f": {ast.unparse(node.args.vararg.annotation)}"
            except Exception:
                pass
        args.append(a)
    elif node.args.kwonlyargs:
        args.append("*")

    for i, arg in enumerate(node.args.kwonlyargs):
        parts = [arg.arg]
        if arg.annotation:
            try:
                parts.append(f": {ast.unparse(arg.annotation)}")
            except Exception:
                pass
        if node.args.kw_defaults[i]:
            try:
                parts.append(f" = {ast.unparse(node.args.kw_defaults[i])}")
            except Exception:
                parts.append(" = ...")
        args.append("".join(parts))

    if node.args.kwarg:
        a = f"**{node.args.kwarg.arg}"
        if node.args.kwarg.annotation:
            try:
                a += f": {ast.unparse(node.args.kwarg.annotation)}"
            except Exception:
                pass
        args.append(a)

    ret = ""
    if node.returns:
        try:
            ret = f" -> {ast.unparse(node.returns)}"
        except Exception:
            pass

    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}def {node.name}({', '.join(args)}){ret}"


def _parse_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    return FunctionInfo(
        name=node.name,
        signature=_build_signature(node),
        docstring=ast.get_docstring(node) or "",
        decorators=[_get_decorator_name(d) for d in node.decorator_list],
        line=node.lineno,
        is_public=not node.name.startswith("_"),
    )


def _parse_class(node: ast.ClassDef) -> ClassInfo:
    bases = []
    for base in node.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            pass

    methods = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_parse_function(child))

    return ClassInfo(
        name=node.name,
        bases=bases,
        docstring=ast.get_docstring(node) or "",
        methods=methods,
        decorators=[_get_decorator_name(d) for d in node.decorator_list],
        line=node.lineno,
        is_public=not node.name.startswith("_"),
    )


def analyze_python(path: Path, relative: str) -> FileInfo:
    source = path.read_text(encoding="utf-8", errors="replace")
    fi = FileInfo(
        path=path, relative=relative, language="Python",
        lines=source.count("\n") + 1,
    )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return fi

    fi.docstring = ast.get_docstring(tree) or ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                fi.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                fi.imports.append(node.module)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            fi.classes.append(_parse_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fi.functions.append(_parse_function(node))

    print(f"  Analyzed {relative} ({len(fi.classes)} classes, {len(fi.functions)} functions)")
    return fi


# ── Regex Analysis (Non-Python) ───────────────────────────────────────────────

REGEX_PATTERNS: dict[str, dict[str, str]] = {
    "TypeScript": {
        "function": r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)",
        "class": r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)",
        "arrow": r"(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>",
        "interface": r"(?:export\s+)?interface\s+(\w+)",
        "type_alias": r"(?:export\s+)?type\s+(\w+)\s*=",
    },
    "JavaScript": {
        "function": r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
        "class": r"(?:export\s+)?class\s+(\w+)",
        "arrow": r"(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
    },
    "Go": {
        "function": r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(([^)]*)\)",
        "struct": r"type\s+(\w+)\s+struct\s*\{",
        "interface": r"type\s+(\w+)\s+interface\s*\{",
    },
    "Java": {
        "class": r"(?:public|private|protected)?\s*(?:abstract\s+)?class\s+(\w+)",
        "method": r"(?:public|private|protected)\s+(?:static\s+)?(?:\w+(?:<[^>]*>)?)\s+(\w+)\s*\(([^)]*)\)",
        "interface": r"(?:public\s+)?interface\s+(\w+)",
    },
    "Rust": {
        "function": r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)",
        "struct": r"(?:pub\s+)?struct\s+(\w+)",
        "trait": r"(?:pub\s+)?trait\s+(\w+)",
        "impl": r"impl(?:<[^>]*>)?\s+(\w+)",
    },
    "Ruby": {
        "class": r"class\s+(\w+)",
        "method": r"def\s+(\w+)",
        "module": r"module\s+(\w+)",
    },
}


def analyze_other(path: Path, relative: str, language: str) -> FileInfo:
    source = path.read_text(encoding="utf-8", errors="replace")
    fi = FileInfo(
        path=path, relative=relative, language=language,
        lines=source.count("\n") + 1,
    )

    patterns = REGEX_PATTERNS.get(language, {})
    if not patterns:
        print(f"  Scanned {relative} (no deep analysis for {language})")
        return fi

    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, source, re.MULTILINE):
            name = match.group(1)
            if kind in ("class", "struct", "interface", "trait", "module", "impl"):
                fi.classes.append(ClassInfo(
                    name=name,
                    line=source[:match.start()].count("\n") + 1,
                    is_public=not name.startswith("_"),
                ))
            else:
                sig = match.group(0).strip()
                if len(sig) > 120:
                    sig = sig[:117] + "..."
                fi.functions.append(FunctionInfo(
                    name=name,
                    signature=sig,
                    line=source[:match.start()].count("\n") + 1,
                    is_public=not name.startswith("_"),
                ))

    print(f"  Scanned {relative} ({len(fi.classes)} types, {len(fi.functions)} functions)")
    return fi


# ── Markdown Generation ───────────────────────────────────────────────────────


def _sanitize_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", name)


def generate_index(repo: RepoMap) -> str:
    lines = [
        f"# {repo.name}",
        "",
        f"Auto-generated documentation for **{repo.name}**.",
        "",
        "## Tech Stack",
        "",
        "| Language | Files | Percentage |",
        "|----------|-------|------------|",
    ]
    for lang, count in sorted(repo.languages.items(), key=lambda x: -x[1]):
        pct = count / repo.total_files * 100 if repo.total_files else 0
        lines.append(f"| {lang} | {count} | {pct:.0f}% |")

    lines += [
        "",
        "## Project Stats",
        "",
        f"- **Total files:** {repo.total_files}",
        f"- **Total lines:** {repo.total_lines:,}",
        f"- **Modules:** {len(repo.modules)}",
    ]

    if repo.config_files:
        lines += ["", "## Configuration", ""]
        for cf in sorted(repo.config_files):
            lines.append(f"- `{cf}`")

    lines += [
        "",
        "## Modules",
        "",
        "| Module | Files | Lines | Primary Language |",
        "|--------|-------|-------|------------------|",
    ]
    for mod in repo.modules:
        lines.append(
            f"| [{mod.name}](modules/{mod.name}.md) | {len(mod.files)} | "
            f"{mod.total_lines:,} | {mod.primary_language} |"
        )

    lines += [
        "",
        "## Quick Start",
        "",
        "Browse the [Architecture](architecture.md) for system shape, ",
        "or dive into individual [module docs](modules/) for details.",
    ]
    return "\n".join(lines)


def generate_architecture(repo: RepoMap) -> str:
    lines = [
        "# Architecture",
        "",
        "## System Diagram",
        "",
        "```mermaid",
        "graph TD",
    ]

    # Build dependency graph from imports
    module_names = {m.name for m in repo.modules}
    edges: set[tuple[str, str]] = set()
    nodes_used: set[str] = set()

    for mod in repo.modules:
        for fi in mod.files:
            for imp in fi.imports:
                # Check if import references another module
                imp_root = imp.split(".")[0]
                if imp_root in module_names and imp_root != mod.name:
                    edges.add((mod.name, imp_root))
                    nodes_used.add(mod.name)
                    nodes_used.add(imp_root)

    # Add all modules as nodes (even if no edges)
    all_nodes = {m.name for m in repo.modules}
    # Limit to ~20 nodes for readability
    if len(all_nodes) > 20:
        # Keep nodes with edges, then fill with largest modules
        remaining = all_nodes - nodes_used
        by_size = sorted(
            [m for m in repo.modules if m.name in remaining],
            key=lambda m: -m.total_lines,
        )
        keep = nodes_used | {m.name for m in by_size[: 20 - len(nodes_used)]}
        all_nodes = keep

    for name in sorted(all_nodes):
        sid = _sanitize_id(name)
        mod = next((m for m in repo.modules if m.name == name), None)
        label = name
        if mod:
            label = f"{name} ({len(mod.files)} files)"
        lines.append(f"    {sid}[\"{label}\"]")

    for src, dst in sorted(edges):
        if src in all_nodes and dst in all_nodes:
            lines.append(f"    {_sanitize_id(src)} --> {_sanitize_id(dst)}")

    lines += [
        "```",
        "",
        "## Module Overview",
        "",
    ]

    for mod in repo.modules:
        if mod.name not in all_nodes:
            continue
        desc = ""
        # Try to get module docstring from __init__.py or main file
        for fi in mod.files:
            if fi.docstring and (fi.relative.endswith("__init__.py") or len(mod.files) == 1):
                desc = fi.docstring.split("\n")[0]
                break
        if not desc:
            desc = f"{mod.primary_language} module with {len(mod.files)} files"
        lines.append(f"- **{mod.name}** — {desc}")

    lines += [
        "",
        "<!-- TODO: Add prose explaining key architectural decisions and tradeoffs -->",
    ]
    return "\n".join(lines)


def generate_data_flows(repo: RepoMap) -> str:
    lines = [
        "# Data Flows",
        "",
        "Key pathways through the system.",
        "",
    ]

    # Identify entry points (CLI commands, main functions, decorated routes)
    entry_points: list[tuple[str, str, str]] = []  # (module, file, function)
    for mod in repo.modules:
        for fi in mod.files:
            for fn in fi.functions:
                is_entry = (
                    fn.name == "main"
                    or any(d in ("click.command", "click.group", "app.route",
                                 "app.get", "app.post", "main.command")
                           for d in fn.decorators)
                    or fn.name.endswith("_cmd")
                )
                if is_entry:
                    entry_points.append((mod.name, fi.relative, fn.name))

    if entry_points:
        lines += [
            "## Entry Points",
            "",
            "| Module | File | Function |",
            "|--------|------|----------|",
        ]
        for mod_name, filepath, func_name in entry_points[:15]:
            lines.append(f"| {mod_name} | `{filepath}` | `{func_name}()` |")

        # Generate a flow diagram for the module with most entry points
        if entry_points:
            # Pick the module with the most entry points
            ep_counts: dict[str, int] = {}
            for mn, _, _ in entry_points:
                ep_counts[mn] = ep_counts.get(mn, 0) + 1
            best_ep_mod = max(ep_counts, key=ep_counts.get)
            lines += [
                "",
                "## Primary Flow",
                "",
                "```mermaid",
                "sequenceDiagram",
            ]
            # Show flow from entry point through modules it imports
            ep_mod_name = best_ep_mod
            ep_mod = next((m for m in repo.modules if m.name == ep_mod_name), None)
            if ep_mod:
                module_names = {m.name for m in repo.modules}
                called: list[str] = []
                for fi in ep_mod.files:
                    for imp in fi.imports:
                        imp_root = imp.split(".")[0]
                        if imp_root in module_names and imp_root != ep_mod_name:
                            if imp_root not in called:
                                called.append(imp_root)

                lines.append(f"    participant User")
                lines.append(f"    participant {ep_mod_name}")
                for c in called[:6]:
                    lines.append(f"    participant {c}")

                lines.append(f"    User->>+{ep_mod_name}: invoke")
                for c in called[:6]:
                    lines.append(f"    {ep_mod_name}->>+{c}: call")
                    lines.append(f"    {c}-->>-{ep_mod_name}: result")
                lines.append(f"    {ep_mod_name}-->>-User: output")

            lines.append("```")
    else:
        lines.append("No obvious entry points detected. Add sequence diagrams manually.")

    lines += [
        "",
        "<!-- TODO: Add sequence diagrams for the 2-3 most important flows -->",
        "<!-- TODO: Explain what triggers each flow and the end state -->",
    ]
    return "\n".join(lines)


def generate_api_reference(repo: RepoMap) -> str:
    lines = [
        "# API Reference",
        "",
        "Public classes and functions across all modules.",
        "",
    ]

    for mod in repo.modules:
        public_classes = []
        public_functions = []
        for fi in mod.files:
            for cls in fi.classes:
                if cls.is_public:
                    public_classes.append((fi.relative, cls))
            for fn in fi.functions:
                if fn.is_public:
                    public_functions.append((fi.relative, fn))

        if not public_classes and not public_functions:
            continue

        lines.append(f"## {mod.name}")
        lines.append("")

        if public_classes:
            for filepath, cls in public_classes:
                bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
                lines.append(f"### `class {cls.name}{bases_str}`")
                lines.append(f"*{filepath}:{cls.line}*")
                lines.append("")
                if cls.docstring:
                    lines.append(cls.docstring.strip())
                    lines.append("")

                public_methods = [m for m in cls.methods if m.is_public]
                if public_methods:
                    lines.append("| Method | Signature |")
                    lines.append("|--------|-----------|")
                    for m in public_methods:
                        sig = m.signature.replace("|", "\\|")
                        lines.append(f"| `{m.name}` | `{sig}` |")
                    lines.append("")

        if public_functions:
            lines.append("### Functions")
            lines.append("")
            lines.append("| Function | Signature | Description |")
            lines.append("|----------|-----------|-------------|")
            for filepath, fn in public_functions:
                sig = fn.signature.replace("|", "\\|")
                doc = fn.docstring.split("\n")[0][:80] if fn.docstring else ""
                doc = doc.replace("|", "\\|")
                lines.append(f"| `{fn.name}` | `{sig}` | {doc} |")
            lines.append("")

    return "\n".join(lines)


def generate_glossary(repo: RepoMap) -> str:
    terms: dict[str, str] = {}

    for mod in repo.modules:
        for fi in mod.files:
            for cls in fi.classes:
                if cls.is_public and cls.docstring:
                    terms[cls.name] = cls.docstring.split("\n")[0]
                elif cls.is_public:
                    terms[cls.name] = f"Class in {mod.name}"

    lines = [
        "# Glossary",
        "",
        "Key terms and concepts in this codebase.",
        "",
        "| Term | Definition |",
        "|------|------------|",
    ]
    for term in sorted(terms):
        defn = terms[term].replace("|", "\\|")
        lines.append(f"| **{term}** | {defn} |")

    lines += [
        "",
        "<!-- TODO: Add domain-specific terms a new engineer would need -->",
    ]
    return "\n".join(lines)


def generate_module_doc(mod: ModuleInfo, repo: RepoMap) -> str:
    lines = [
        f"# {mod.name}",
        "",
    ]

    # Module-level docstring
    main_doc = ""
    for fi in mod.files:
        if fi.docstring and (fi.relative.endswith("__init__.py") or len(mod.files) == 1):
            main_doc = fi.docstring
            break
    if main_doc:
        lines += [main_doc.strip(), ""]
    else:
        lines += [f"*{mod.primary_language} module — {len(mod.files)} files, {mod.total_lines:,} lines*", ""]

    # Files
    lines += [
        "## Files",
        "",
        "| File | Lines | Classes | Functions |",
        "|------|-------|---------|-----------|",
    ]
    for fi in sorted(mod.files, key=lambda f: f.relative):
        fname = fi.relative.split("/")[-1]
        lines.append(f"| `{fname}` | {fi.lines} | {len(fi.classes)} | {len(fi.functions)} |")
    lines.append("")

    # Internal dependencies
    module_names = {m.name for m in repo.modules}
    # Build set of filenames in this module (without extension) for intra-module detection
    mod_filenames = set()
    for fi in mod.files:
        stem = Path(fi.relative).stem
        mod_filenames.add(stem)

    internal_deps: set[str] = set()
    external_deps: set[str] = set()
    intra_deps: set[str] = set()
    for fi in mod.files:
        for imp in fi.imports:
            imp_root = imp.split(".")[0]
            if imp_root in module_names and imp_root != mod.name:
                internal_deps.add(imp_root)
            elif imp_root in mod_filenames and imp_root != Path(fi.relative).stem:
                # Intra-module import (e.g., "from base import ..." within synthkit)
                intra_deps.add(imp_root)
            elif imp_root != mod.name and imp_root not in mod_filenames:
                external_deps.add(imp_root)

    if internal_deps:
        lines += ["## Internal Dependencies", ""]
        for dep in sorted(internal_deps):
            lines.append(f"- [{dep}]({dep}.md)")
        lines.append("")

    if intra_deps:
        lines += ["## Intra-module Dependencies", ""]
        for dep in sorted(intra_deps):
            lines.append(f"- `{dep}` (within this module)")
        lines.append("")

    # Filter out stdlib modules from external deps
    stdlib = {
        "abc", "argparse", "ast", "asyncio", "base64", "collections", "configparser",
        "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal", "enum",
        "errno", "functools", "glob", "hashlib", "hmac", "html", "http", "importlib",
        "inspect", "io", "itertools", "json", "logging", "math", "multiprocessing",
        "operator", "os", "pathlib", "pickle", "platform", "pprint", "queue", "random",
        "re", "secrets", "shutil", "signal", "socket", "sqlite3", "string", "struct",
        "subprocess", "sys", "tempfile", "textwrap", "threading", "time", "timeit",
        "traceback", "typing", "unittest", "urllib", "uuid", "warnings", "weakref", "xml",
    }
    third_party = sorted(d for d in external_deps if d not in stdlib)
    if third_party:
        lines += ["## External Dependencies", ""]
        for dep in third_party[:20]:
            lines.append(f"- `{dep}`")
        lines.append("")

    # Module diagram
    all_symbols: list[str] = []
    for fi in mod.files:
        fname = fi.relative.split("/")[-1].replace(".py", "").replace(".", "_")
        for cls in fi.classes[:5]:
            all_symbols.append((_sanitize_id(f"{fname}_{cls.name}"), cls.name, "class"))
        for fn in fi.functions[:5]:
            if fn.is_public:
                all_symbols.append((_sanitize_id(f"{fname}_{fn.name}"), fn.name, "function"))

    if all_symbols and len(all_symbols) <= 20:
        lines += [
            "## Structure",
            "",
            "```mermaid",
            "graph LR",
        ]
        for sid, label, kind in all_symbols:
            if kind == "class":
                lines.append(f"    {sid}[[\"{label}\"]]")
            else:
                lines.append(f"    {sid}(\"{label}\")")
        lines += ["```", ""]

    # Detailed file sections
    for fi in sorted(mod.files, key=lambda f: f.relative):
        fname = fi.relative.split("/")[-1]
        lines.append(f"## {fname}")
        lines.append("")

        if fi.docstring:
            lines += [fi.docstring.strip(), ""]

        for cls in fi.classes:
            bases = f" ({', '.join(cls.bases)})" if cls.bases else ""
            lines.append(f"### class `{cls.name}`{bases}")
            lines.append("")
            if cls.docstring:
                lines += [cls.docstring.strip(), ""]
            if cls.methods:
                public = [m for m in cls.methods if m.is_public]
                if public:
                    lines.append("**Methods:**")
                    lines.append("")
                    for m in public:
                        doc = f" — {m.docstring.split(chr(10))[0]}" if m.docstring else ""
                        lines.append(f"- `{m.signature}`{doc}")
                    lines.append("")

        if fi.functions:
            public_fns = [f for f in fi.functions if f.is_public]
            if public_fns:
                lines.append("**Functions:**")
                lines.append("")
                for fn in public_fns:
                    doc = f" — {fn.docstring.split(chr(10))[0]}" if fn.docstring else ""
                    lines.append(f"- `{fn.signature}`{doc}")
                lines.append("")

    lines += [
        "<!-- TODO: Explain this module's role, key abstractions, and non-obvious behavior -->",
    ]
    return "\n".join(lines)


# ── HTML Site Generation ──────────────────────────────────────────────────────


def generate_site(docs_dir: Path, repo_name: str) -> str:
    # Read all generated markdown files
    pages: dict[str, dict[str, str]] = {}
    page_order: list[str] = []

    general_order = ["index", "architecture", "data-flows", "api-reference", "glossary"]
    for name in general_order:
        md_path = docs_dir / f"{name}.md"
        if md_path.exists():
            content = md_path.read_text(encoding="utf-8")
            title = content.split("\n")[0].lstrip("# ").strip() if content else name
            pages[name] = {"title": title, "section": "General", "content": content}
            page_order.append(name)

    modules_dir = docs_dir / "modules"
    if modules_dir.is_dir():
        for md_path in sorted(modules_dir.glob("*.md")):
            key = f"modules/{md_path.stem}"
            content = md_path.read_text(encoding="utf-8")
            title = content.split("\n")[0].lstrip("# ").strip() if content else md_path.stem
            pages[key] = {"title": title, "section": "Modules", "content": content}
            page_order.append(key)

    pages_json = json.dumps(pages, ensure_ascii=False)
    order_json = json.dumps(page_order)

    return HTML_TEMPLATE.replace("__PAGES_DATA__", pages_json).replace(
        "__PAGE_ORDER__", order_json
    ).replace("__REPO_NAME__", repo_name)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__REPO_NAME__ — Wiki</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/styles/github-dark.min.css">
<style>
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #1c2128;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --text-heading: #f0f6fc;
    --accent: #58a6ff;
    --accent-dim: #1f6feb;
    --border: #30363d;
    --sidebar-w: 280px;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg-primary); color: var(--text-primary); line-height: 1.6;
}
/* Sidebar */
.sidebar {
    position: fixed; left:0; top:0; bottom:0; width: var(--sidebar-w);
    background: var(--bg-secondary); border-right: 1px solid var(--border);
    overflow-y: auto; display: flex; flex-direction: column;
}
.sidebar-header {
    padding: 1.2rem 1rem 0.8rem; border-bottom: 1px solid var(--border);
}
.sidebar-header h1 { font-size: 1.1rem; color: var(--text-heading); font-weight: 600; }
.sidebar-header p { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem; }
.sidebar-search { padding: 0.6rem 0.8rem; }
.sidebar-search input {
    width: 100%; padding: 0.45rem 0.7rem; background: var(--bg-tertiary);
    border: 1px solid var(--border); border-radius: 6px; color: var(--text-primary);
    font-size: 0.85rem; outline: none;
}
.sidebar-search input:focus { border-color: var(--accent); }
.sidebar-nav { flex:1; overflow-y: auto; padding: 0.3rem 0; }
.nav-section {
    padding: 0.6rem 1rem 0.25rem; font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-secondary); font-weight: 600;
}
.nav-item {
    display: block; padding: 0.3rem 1rem 0.3rem 1.4rem; color: var(--text-secondary);
    text-decoration: none; font-size: 0.87rem; cursor: pointer;
    border-left: 2px solid transparent; transition: all 0.12s;
}
.nav-item:hover { color: var(--text-primary); background: var(--bg-tertiary); }
.nav-item.active {
    color: var(--accent); background: rgba(88,166,255,0.08);
    border-left-color: var(--accent);
}
.search-results { padding: 0.3rem 0; }
.search-result {
    padding: 0.35rem 1rem 0.35rem 1.4rem; cursor: pointer;
    color: var(--text-secondary); font-size: 0.85rem;
}
.search-result:hover { color: var(--accent); background: var(--bg-tertiary); }
.search-result em { font-style: normal; color: var(--accent); }

/* Content */
.content {
    margin-left: var(--sidebar-w); padding: 2.5rem 3rem; max-width: 960px;
}
.content h1 {
    font-size: 2rem; color: var(--text-heading); margin: 0 0 1rem;
    padding-bottom: 0.5rem; border-bottom: 1px solid var(--border);
}
.content h2 {
    font-size: 1.4rem; color: var(--text-heading); margin: 2rem 0 0.6rem;
    padding-bottom: 0.3rem; border-bottom: 1px solid var(--border);
}
.content h3 { font-size: 1.15rem; color: var(--text-heading); margin: 1.5rem 0 0.4rem; }
.content h4 { font-size: 1rem; color: var(--text-heading); margin: 1.2rem 0 0.3rem; }
.content p { margin: 0.5rem 0; }
.content ul, .content ol { margin: 0.5rem 0 0.5rem 1.5rem; }
.content li { margin: 0.2rem 0; }
.content code {
    background: var(--bg-tertiary); padding: 0.15em 0.4em; border-radius: 4px;
    font-size: 0.85em; font-family: "SFMono-Regular", Consolas, monospace;
}
.content pre {
    background: var(--bg-tertiary); padding: 1rem; border-radius: 8px;
    overflow-x: auto; margin: 1rem 0; border: 1px solid var(--border);
}
.content pre code { background: none; padding: 0; font-size: 0.82em; }
.content table { width: 100%; border-collapse: collapse; margin: 0.8rem 0; }
.content th, .content td {
    padding: 0.45rem 0.7rem; border: 1px solid var(--border); text-align: left;
    font-size: 0.9rem;
}
.content th { background: var(--bg-secondary); color: var(--text-heading); font-weight: 600; }
.content a { color: var(--accent); text-decoration: none; }
.content a:hover { text-decoration: underline; }
.content blockquote {
    border-left: 3px solid var(--accent-dim); padding-left: 1rem;
    color: var(--text-secondary); margin: 0.8rem 0;
}
.content hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
.content img { max-width: 100%; border-radius: 8px; }
.mermaid {
    background: var(--bg-tertiary); padding: 1.2rem; border-radius: 8px;
    margin: 1rem 0; text-align: center;
}

/* Mobile */
@media (max-width: 768px) {
    .sidebar { width: 100%; height: auto; position: relative; border-right: none; border-bottom: 1px solid var(--border); }
    .content { margin-left: 0; padding: 1.5rem 1rem; }
    .sidebar-nav { max-height: 50vh; }
}
</style>
</head>
<body>

<div class="sidebar">
    <div class="sidebar-header">
        <h1>__REPO_NAME__</h1>
        <p>Generated Documentation</p>
    </div>
    <div class="sidebar-search">
        <input type="text" id="search-input" placeholder="Search docs...">
    </div>
    <div id="search-results" class="search-results" style="display:none"></div>
    <div id="nav" class="sidebar-nav"></div>
</div>

<div id="content" class="content">
    <p>Loading...</p>
</div>

<script src="https://cdn.jsdelivr.net/npm/marked@14/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7/dist/fuse.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/highlight.min.js"></script>
<script>
const PAGES = __PAGES_DATA__;
const PAGE_ORDER = __PAGE_ORDER__;

mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });

function buildNav() {
    const nav = document.getElementById('nav');
    let html = '', lastSection = '';
    PAGE_ORDER.forEach(key => {
        const page = PAGES[key];
        if (page.section !== lastSection) {
            html += '<div class="nav-section">' + page.section + '</div>';
            lastSection = page.section;
        }
        html += '<a class="nav-item" data-page="' + key + '">' + page.title + '</a>';
    });
    nav.innerHTML = html;
    nav.querySelectorAll('.nav-item').forEach(el => {
        el.addEventListener('click', () => navigateTo(el.dataset.page));
    });
}

async function navigateTo(key) {
    const content = document.getElementById('content');
    content.innerHTML = marked.parse(PAGES[key].content);

    // Active nav
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.page === key);
    });

    // Render mermaid
    const mermaidBlocks = content.querySelectorAll('pre code.language-mermaid');
    let mermaidId = 0;
    mermaidBlocks.forEach(el => {
        const div = document.createElement('div');
        div.className = 'mermaid';
        div.id = 'mermaid-' + (mermaidId++);
        div.textContent = el.textContent;
        el.parentElement.replaceWith(div);
    });
    if (mermaidBlocks.length > 0) {
        try { await mermaid.run({ querySelector: '.mermaid' }); } catch(e) { console.warn('Mermaid:', e); }
    }

    // Highlight code
    content.querySelectorAll('pre code:not(.language-mermaid)').forEach(el => {
        hljs.highlightElement(el);
    });

    window.scrollTo(0, 0);
    history.replaceState(null, '', '#' + key);
}

function initSearch() {
    const data = PAGE_ORDER.map(key => ({
        key, title: PAGES[key].title,
        content: PAGES[key].content.substring(0, 2000),
    }));
    const fuse = new Fuse(data, { keys: ['title', 'content'], threshold: 0.3 });

    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    const nav = document.getElementById('nav');

    input.addEventListener('input', () => {
        const q = input.value.trim();
        if (!q) { results.style.display='none'; nav.style.display='block'; return; }
        const matches = fuse.search(q).slice(0, 8);
        results.style.display = 'block'; nav.style.display = 'none';
        results.innerHTML = matches.map(m =>
            '<div class="search-result" data-page="' + m.item.key + '">' + m.item.title + '</div>'
        ).join('');
        results.querySelectorAll('.search-result').forEach(el => {
            el.addEventListener('click', () => {
                navigateTo(el.dataset.page);
                input.value = '';
                results.style.display = 'none';
                nav.style.display = 'block';
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    buildNav();
    initSearch();
    const hash = location.hash.slice(1);
    navigateTo(hash && PAGES[hash] ? hash : PAGE_ORDER[0]);
});
</script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a wiki from a code repository.")
    parser.add_argument("--repo-path", default=".", help="Path to repository root (default: cwd)")
    parser.add_argument("--output-path", default="./wiki", help="Output directory (default: ./wiki)")
    parser.add_argument("--rebuild-site", action="store_true",
                        help="Only rebuild the HTML site from existing docs/")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    output_path = Path(args.output_path)
    docs_dir = output_path / "docs"
    site_dir = output_path / "site"

    project_name = _detect_project_name(repo_path)

    if args.rebuild_site:
        if not docs_dir.exists():
            print(f"Error: {docs_dir} not found. Run without --rebuild-site first.")
            sys.exit(1)
        print("Rebuilding HTML site from existing docs...")
        site_dir.mkdir(parents=True, exist_ok=True)
        html = generate_site(docs_dir, project_name)
        (site_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"Site rebuilt at {site_dir / 'index.html'}")
        return

    # Full generation
    print(f"\n{'=' * 60}")
    print(f"  Mapping: {project_name}")
    print(f"{'=' * 60}\n")

    repo = discover_repo(repo_path)

    docs_dir.mkdir(parents=True, exist_ok=True)
    modules_dir = docs_dir / "modules"
    modules_dir.mkdir(exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)

    # Generate markdown docs
    print("\nGenerating documentation...")

    doc_files = {
        "index.md": generate_index(repo),
        "architecture.md": generate_architecture(repo),
        "data-flows.md": generate_data_flows(repo),
        "api-reference.md": generate_api_reference(repo),
        "glossary.md": generate_glossary(repo),
    }

    for filename, content in doc_files.items():
        (docs_dir / filename).write_text(content, encoding="utf-8")
        print(f"  Created docs/{filename}")

    for mod in repo.modules:
        content = generate_module_doc(mod, repo)
        (modules_dir / f"{mod.name}.md").write_text(content, encoding="utf-8")
        print(f"  Created docs/modules/{mod.name}.md")

    # Generate HTML site
    print("\nBuilding HTML site...")
    html = generate_site(docs_dir, repo.name)
    (site_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"  Created site/index.html")

    print(f"\n{'=' * 60}")
    print(f"  Wiki generated. Open {site_dir / 'index.html'} to browse.")
    print(f"  {repo.total_files} files, {len(repo.modules)} modules, {repo.total_lines:,} lines")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
