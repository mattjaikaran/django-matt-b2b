#!/usr/bin/env python3
"""Agent docs check for the pre-commit hook and CI.

Fails when:

  - `AGENTS.md` is missing at the repo root;
  - `CLAUDE.md` exists but does not import `AGENTS.md` (`@AGENTS.md`);
  - a relative link in a checked Markdown file does not resolve.

Absolute URLs, `mailto:` links and in-page anchors are skipped, as are links
inside fenced code blocks and inline code.

Usage:
    python3 scripts/check_agent_docs.py [file ...]

With no arguments it checks AGENTS.md, CLAUDE.md and every Markdown file under
docs/, tasks/ and .claude/skills/. The pre-commit hook passes the changed
files.

Exit: 0 pass, 1 a check failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
CLAUDE = ROOT / "CLAUDE.md"
DEFAULT_GLOBS = ("docs/**/*.md", "tasks/**/*.md", ".claude/skills/**/*.md")
IMPORT_LINE = re.compile(r"^@AGENTS\.md\s*$", re.MULTILINE)
LINK = re.compile(r"\[[^\]]*\]\(([^)\n]*)\)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def display(path: Path) -> str:
    """Path relative to the repo root when possible."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def default_files() -> list[Path]:
    """AGENTS.md, CLAUDE.md and every Markdown file that documents the agent setup."""
    files = [AGENTS]
    if CLAUDE.is_file():
        files.append(CLAUDE)
    for pattern in DEFAULT_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    return files


def link_target(raw: str) -> str | None:
    """The destination of a Markdown link, or None when it is empty."""
    target = raw.strip()
    if target.startswith("<"):
        end = target.find(">")
        if end == -1:
            return None
        target = target[1:end]
    elif target:
        target = target.split()[0]  # drop an optional "title"
    return target or None


def check_links(path: Path) -> list[str]:
    """One message per relative link that does not resolve."""
    problems: list[str] = []
    fence = ""
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if fence:
            if stripped.startswith(fence):
                fence = ""
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            continue
        for raw in LINK.findall(INLINE_CODE.sub("", line)):
            target = link_target(raw)
            if target is None or target.startswith("#"):
                continue
            if SCHEME.match(target) or target.startswith("//"):
                continue
            relative = unquote(target.split("#", 1)[0])
            if not relative:
                continue
            resolved = (path.parent / relative).resolve()
            if not resolved.exists():
                problems.append(f"{display(path)}:{number}: {target} does not resolve")
    return problems


def main(argv: list[str]) -> int:
    """Run the check over the given files, or the documented defaults."""
    problems: list[str] = []

    if not AGENTS.is_file():
        problems.append("AGENTS.md is missing at the repo root")

    if CLAUDE.is_file() and not IMPORT_LINE.search(CLAUDE.read_text(encoding="utf-8")):
        problems.append("CLAUDE.md must contain a line '@AGENTS.md'")

    if argv:
        files = [Path(arg).resolve() for arg in argv]
        missing = [path for path in files if not path.is_file()]
        problems.extend(f"{display(path)}: file does not exist" for path in missing)
        files = [path for path in files if path.is_file()]
    else:
        files = [path for path in default_files() if path.is_file()]

    for path in files:
        problems.extend(check_links(path))

    if problems:
        print("Agent docs check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    print(f"Agent docs check passed ({len(files)} file(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
