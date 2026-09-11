"""
Bit-Logger Text Corruption & Mojibake Auditor
Detects and reports UTF-8 encoding corruptions, double-encoded entities, and broken quotes/dashes.
Module: test_helper_scripts/parse_mojibake.py
"""

import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Common mojibake / encoding corruption signatures
MOJIBAKE_SIGNATURES: Dict[str, str] = {
    "â€™": "Corrupted Right Single Quote (’)",
    "â€˜": "Corrupted Left Single Quote (‘)",
    "â€œ": "Corrupted Left Double Quote (“)",
    "â€\x9d": "Corrupted Right Double Quote (”)",
    "â€": "Corrupted Double Quote / Dash prefix",
    "Ã¢â‚¬â„¢": "Double-corrupted Apostrophe (’)",
    "Ã¢â‚¬Å“": "Double-corrupted Left Double Quote (“)",
    "Ã¢â‚¬\x9d": "Double-corrupted Right Double Quote (”)",
    "Ã¢â‚¬â€”": "Double-corrupted Em Dash (—)",
    "Ã¢â‚¬â€“": "Double-corrupted En Dash (–)",
    "â€”": "Corrupted Em Dash (—)",
    "â€“": "Corrupted En Dash (–)",
    "Ã©": "Corrupted 'é'",
    "Ã¡": "Corrupted 'á'",
    "Ã³": "Corrupted 'ó'",
    "Ãº": "Corrupted 'ú'",
    "Ã±": "Corrupted 'ñ'",
    "Ã§": "Corrupted 'ç'",
    "Ã¨": "Corrupted 'è'",
    "Ã\xa0": "Corrupted 'à'",
    "Ã¹": "Corrupted 'ù'",
    "Ã¼": "Corrupted 'ü'",
    "Ã¤": "Corrupted 'ä'",
    "Ã¶": "Corrupted 'ö'",
    "ÃŸ": "Corrupted 'ß'",
}

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "test_helper_scripts",
}

SCANNED_EXTENSIONS = {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".sql", ".sh", ".html", ".css"}


@dataclass
class MojibakeFinding:
    line_number: int
    line_content: str
    matches: Dict[str, str]


@dataclass
class FileCorruptionRecord:
    file_path: str
    rel_path: str
    findings: List[MojibakeFinding] = field(default_factory=list)


@dataclass
class MojibakeAuditSummary:
    total_files_scanned: int = 0
    corrupted_files_count: int = 0
    total_corruptions_found: int = 0
    corrupted_records: List[FileCorruptionRecord] = field(default_factory=list)


def scan_file_for_mojibake(file_path: str, rel_path: str) -> Optional[FileCorruptionRecord]:
    """Scans a single file line-by-line for known mojibake signatures."""
    base_name = os.path.basename(file_path)
    if base_name in ("parse_mojibake.py", "text_normalizer.py", "test_mojibake.py"):
        return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return None

    findings: List[MojibakeFinding] = []

    for idx, line in enumerate(lines, start=1):
        line_matches: Dict[str, str] = {}
        for sig, description in MOJIBAKE_SIGNATURES.items():
            if sig in line:
                line_matches[sig] = description

        if line_matches:
            findings.append(
                MojibakeFinding(
                    line_number=idx,
                    line_content=line.strip(),
                    matches=line_matches,
                )
            )

    if findings:
        return FileCorruptionRecord(
            file_path=os.path.abspath(file_path),
            rel_path=rel_path,
            findings=findings,
        )
    return None


def run_mojibake_audit(
    root_dir: str = ".",
    ignore_helper_scripts: bool = True,
) -> MojibakeAuditSummary:
    """Scans codebase files for text corruption and mojibake signatures."""
    summary = MojibakeAuditSummary()
    ignored = set(IGNORED_DIRS)
    if not ignore_helper_scripts:
        ignored.discard("test_helper_scripts")

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored]

        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
            if ext in SCANNED_EXTENSIONS:
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, root_dir)

                summary.total_files_scanned += 1
                record = scan_file_for_mojibake(full_path, rel_path)
                if record:
                    summary.corrupted_files_count += 1
                    summary.total_corruptions_found += len(record.findings)
                    summary.corrupted_records.append(record)

    return summary


def print_mojibake_report(summary: MojibakeAuditSummary) -> None:
    """Prints a structured diagnostic report for mojibake findings."""
    print("=" * 80)
    print(" [TEXT ENCODING] BIT-LOGGER TEXT CORRUPTION & MOJIBAKE AUDIT")
    print("=" * 80)
    print(f"Total Files Scanned      : {summary.total_files_scanned}")
    print(f"Corrupted Files Detected : {summary.corrupted_files_count}")
    print(f"Total Corrupted Lines    : {summary.total_corruptions_found}")
    print("-" * 80)

    if summary.corrupted_files_count == 0:
        print("[PASS] No text corruption or mojibake patterns detected.")
        print("=" * 80)
        return

    print("[WARN] CORRUPTED TEXT / MOJIBAKE DETECTED IN CODEBASE:")
    for record in summary.corrupted_records:
        print(f"\nFile: {record.rel_path}")
        for finding in record.findings:
            print(f"  Line {finding.line_number}: {finding.line_content}")
            for sig, desc in finding.matches.items():
                print(f"    -> Signature: '{sig}' ({desc})")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audit codebase for mojibake / encoding corruption.")
    parser.add_argument("--root", type=str, default=".", help="Root directory to scan (default: .)")
    args = parser.parse_args()

    audit_summary = run_mojibake_audit(root_dir=args.root)
    print_mojibake_report(audit_summary)
    sys.exit(0 if audit_summary.corrupted_files_count == 0 else 1)
