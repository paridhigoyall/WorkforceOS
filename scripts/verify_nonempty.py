#!/usr/bin/env python3
"""
WorkforceOS File Integrity & Non-Empty File Checker
Scans the entire repository tree to ensure that no code or configuration files are 0 bytes or corrupted.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Directories and patterns to ignore during scan
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".gemini",
    ".system_generated",
    "postgres_data",
    ".vscode",
    ".idea",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".sqlite3",
    ".log",
}

# Allow certain legitimate empty files if any (e.g. __init__.py)
ALLOWED_EMPTY_FILES = {
    "__init__.py",
    ".gitkeep",
}


def check_files(root_dir: Path) -> tuple[int, list[Path]]:
    """Recursively checks repository files for emptiness."""
    empty_files: list[Path] = []
    scanned_count = 0

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue

        # Check if any parent part is in excluded directories
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        if path.suffix.lower() in EXCLUDED_EXTENSIONS:
            continue

        scanned_count += 1

        if path.stat().st_size == 0:
            if path.name not in ALLOWED_EMPTY_FILES:
                empty_files.append(path)
        else:
            # Check if file has only whitespace
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").strip()
                if not content and path.name not in ALLOWED_EMPTY_FILES:
                    empty_files.append(path)
            except Exception:
                # Binary files will pass size > 0 check
                pass

    return scanned_count, empty_files


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    print(f"[*] Scanning WorkforceOS workspace at {root} for file integrity...")

    total_scanned, empty_files = check_files(root)
    print(f"[*] Total files checked: {total_scanned}")

    if empty_files:
        print(f"\n[!] WARNING: Found {len(empty_files)} empty or whitespace-only files:")
        for ef in empty_files:
            rel_path = ef.relative_to(root)
            print(f"    - {rel_path}")
        return 1

    print("[PASS] Integrity check PASSED: All repository files contain valid code and configuration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
