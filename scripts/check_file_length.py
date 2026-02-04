#!/usr/bin/env python3
"""
Pre-commit hook to check file length.

Files should not exceed MAX_LINES (default 400).
Prefer files under 200-300 lines.

Add `# file-length-ignore` comment at the top of a file to skip checking.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Configuration
MAX_LINES = 400
WARNING_LINES = 300
IGNORE_COMMENT = "# file-length-ignore"

# File patterns to check
INCLUDE_PATTERNS = ["*.py"]
EXCLUDE_PATTERNS = [
    "**/migrations/*.py",
    "**/__pycache__/**",
    ".venv/**",
    "venv/**",
    "**/node_modules/**",
    "build/**",
    "dist/**",
]


def should_check_file(filepath: Path) -> bool:
    """Check if file should be checked based on patterns."""
    # Check exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if filepath.match(pattern):
            return False

    # Check include patterns
    for pattern in INCLUDE_PATTERNS:
        if filepath.match(pattern):
            return True

    return False


def has_ignore_comment(filepath: Path) -> bool:
    """Check if file has the ignore comment at the top."""
    try:
        with open(filepath, encoding="utf-8") as f:
            # Check first 10 lines for ignore comment
            for i, line in enumerate(f):
                if i >= 10:
                    break
                if IGNORE_COMMENT in line:
                    return True
    except (OSError, UnicodeDecodeError):
        pass
    return False


def count_lines(filepath: Path) -> int:
    """Count lines in a file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0


def main() -> int:
    """Run the file length check."""
    files = sys.argv[1:] if len(sys.argv) > 1 else []

    if not files:
        # If no files provided, check all files in current directory
        files = [str(p) for p in Path(".").rglob("*.py")]

    errors = []
    warnings = []

    for file_str in files:
        filepath = Path(file_str)

        if not filepath.exists():
            continue

        if not should_check_file(filepath):
            continue

        if has_ignore_comment(filepath):
            continue

        line_count = count_lines(filepath)

        if line_count > MAX_LINES:
            errors.append(f"ERROR: {filepath} has {line_count} lines (max: {MAX_LINES})")
        elif line_count > WARNING_LINES:
            warnings.append(f"WARNING: {filepath} has {line_count} lines (prefer < {WARNING_LINES})")

    # Print results
    for warning in warnings:
        print(warning)

    for error in errors:
        print(error)

    if errors:
        print(f"\n{len(errors)} file(s) exceed the maximum line limit of {MAX_LINES}.")
        print("Consider breaking up large files into smaller, focused modules.")
        print(f"Add '{IGNORE_COMMENT}' at the top of a file to bypass this check.")
        return 1

    if warnings:
        print(f"\n{len(warnings)} file(s) are approaching the limit. Consider refactoring.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
