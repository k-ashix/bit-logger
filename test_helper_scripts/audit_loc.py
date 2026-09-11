"""
Bit-Logger Architecture LOC Auditor
Enforces strict modularity and anti-god-file policy:
No single file should exceed 100 LOC. Flags oversized files for decoupling.
Module: test_helper_scripts/audit_loc.py
"""

import os
import sys
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

IGNORED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    ".agents",
    "test_helper_scripts",
}

DEFAULT_EXTENSIONS = {".py", ".sh", ".sql", ".js", ".ts", ".html", ".css"}


@dataclass
class FileLocRecord:
    path: str
    rel_path: str
    total_loc: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    exceeds_limit: bool


def analyze_file_loc(file_path: str, max_loc: int = 100) -> Optional[FileLocRecord]:
    """Analyzes line counts and classification for a single source file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return None

    total_loc = len(lines)
    code_lines = 0
    comment_lines = 0
    blank_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
            comment_lines += 1
        else:
            code_lines += 1

    return FileLocRecord(
        path=os.path.abspath(file_path),
        rel_path=file_path,
        total_loc=total_loc,
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        exceeds_limit=total_loc > max_loc,
    )


def run_architecture_loc_audit(
    root_dir: str = ".",
    max_loc: int = 100,
    extensions: Optional[set] = None,
) -> Tuple[List[FileLocRecord], List[FileLocRecord]]:
    """
    Recursively scans the codebase and audits each file against the maximum LOC limit.
    Returns (all_scanned_files, oversized_files).
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    all_records: List[FileLocRecord] = []
    oversized_records: List[FileLocRecord] = []

    ignored = set(IGNORED_DIRS)
    ignored.discard("test_helper_scripts")
    root_helper_dir = os.path.normpath(os.path.join(root_dir, "test_helper_scripts"))

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [
            d for d in dirs
            if d not in ignored and os.path.normpath(os.path.join(root, d)) != root_helper_dir
        ]

        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
            if ext in extensions:
                full_path = os.path.join(root, file_name)
                record = analyze_file_loc(full_path, max_loc=max_loc)
                if record:
                    all_records.append(record)
                    if record.exceeds_limit:
                        oversized_records.append(record)

    # Sort descending by LOC
    oversized_records.sort(key=lambda r: r.total_loc, reverse=True)
    all_records.sort(key=lambda r: r.total_loc, reverse=True)
    return all_records, oversized_records


def print_audit_report(all_records: List[FileLocRecord], oversized_records: List[FileLocRecord], max_loc: int = 100) -> None:
    """Renders formatted console diagnostic output for the LOC audit."""
    print("=" * 80)
    print(" [MODULARITY] BIT-LOGGER ARCHITECTURE LOC AUDIT (ANTI-GOD-FILE)")
    print(f" Target LOC Threshold: max {max_loc} LOC per file")
    print("=" * 80)

    print(f"Total Scanned Files: {len(all_records)}")
    print(f"Files Within Limit : {len(all_records) - len(oversized_records)}")
    print(f"Files Exceeding    : {len(oversized_records)}")
    print("-" * 80)

    if not oversized_records:
        print("[PASS] All files adhere to the strict <= 100 LOC modularity standard!")
        print("=" * 80)
        return

    print("[WARN] DECOUPLING NEEDED! The following files violate modularity rules:")
    print("-" * 80)
    print(f"{'LOC':<8} {'Code':<8} {'Blank':<8} {'Location'}")
    print("-" * 80)
    for record in oversized_records:
        print(f"{record.total_loc:<8} {record.code_lines:<8} {record.blank_lines:<8} {record.rel_path}")
        print(f"   └──> [ACTION REQUIRED]: Decompose into independent sub-modules or services.")

    print("=" * 80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audit codebase for files exceeding LOC limits.")
    parser.add_argument("--max-loc", type=int, default=100, help="Maximum allowed LOC per file (default: 100)")
    parser.add_argument("--root", type=str, default=".", help="Root directory to audit (default: .)")
    args = parser.parse_args()

    all_files, violations = run_architecture_loc_audit(root_dir=args.root, max_loc=args.max_loc)
    print_audit_report(all_files, violations, max_loc=args.max_loc)
    sys.exit(0 if len(violations) == 0 else 1)
