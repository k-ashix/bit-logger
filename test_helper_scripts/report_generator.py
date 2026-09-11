"""
Bit-Logger Forensic Report & Log Generator
Generates dual timestamped outputs:
  - master_run_{timestamp}.log (raw execution telemetry)
  - master_run_{timestamp}.md  (rich markdown audit report)
Module: test_helper_scripts/report_generator.py
"""

import os
import io
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple


class DualLogger:
    """Captures stream output to both console and memory buffer for log file export."""

    def __init__(self, original_stdout) -> None:
        self.original_stdout = original_stdout
        self.buffer = io.StringIO()

    def write(self, message: str) -> None:
        self.original_stdout.write(message)
        self.buffer.write(message)

    def flush(self) -> None:
        self.original_stdout.flush()

    def get_logs(self) -> str:
        return self.buffer.getvalue()


def get_timestamp_str() -> str:
    """Generates standard timestamp string for filenames (YYYYMMDD_HH_MM_AM/PM in 12-hr IST, no seconds)."""
    return datetime.now().strftime("%Y%m%d_%I_%M_%p")


def get_date_str() -> str:
    """Generates standard date string for daily folder (YYYY_MM_DD)."""
    return datetime.now().strftime("%Y_%m_%d")


def get_time_str() -> str:
    """Generates standard 12-hour time string for run folder (HH_MM_AM/PM in 12-hr IST, no seconds)."""
    return datetime.now().strftime("%I_%M_%p")


def ensure_logs_dir(base_dir: str = ".") -> str:
    """Ensures test_helper_scripts/logs directory exists and returns its path."""
    norm = os.path.normpath(os.path.abspath(base_dir))
    if os.path.basename(norm) == "test_helper_scripts":
        logs_dir = os.path.join(base_dir, "logs")
    elif os.path.basename(norm) == "logs" and os.path.basename(os.path.dirname(norm)) == "test_helper_scripts":
        logs_dir = base_dir
    else:
        logs_dir = os.path.join(base_dir, "test_helper_scripts", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def ensure_run_dir(
    base_dir: str = ".",
    timestamp_str: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Creates a hierarchical run folder under test_helper_scripts/logs/run_{YYYY_MM_DD}/run_{HH_MM_AM/PM}/
    using 12-hour Indian clock format with AM/PM and without seconds to prevent collisions.
    Reuses the existing date folder for subsequent runs on the same date.
    Returns (run_dir_path, timestamp_str, date_dir_path).
    """
    logs_dir = ensure_logs_dir(base_dir)

    if timestamp_str is None:
        now = datetime.now()
        date_str = now.strftime("%Y_%m_%d")
        time_str = now.strftime("%I_%M_%p")
        timestamp_str = f"{now.strftime('%Y%m%d')}_{time_str}"
    else:
        parts = timestamp_str.split("_", 1)
        raw_date = parts[0]
        if len(raw_date) == 8 and raw_date.isdigit():
            date_str = f"{raw_date[:4]}_{raw_date[4:6]}_{raw_date[6:8]}"
        else:
            date_str = get_date_str()
        time_str = parts[1] if len(parts) > 1 else get_time_str()

    date_dir = os.path.join(logs_dir, f"run_{date_str}")
    os.makedirs(date_dir, exist_ok=True)

    run_dir = os.path.join(date_dir, f"run_{time_str}")
    os.makedirs(run_dir, exist_ok=True)

    return run_dir, timestamp_str, date_dir


def write_log_file(target_dir: str, timestamp_str: str, raw_content: str) -> str:
    """Writes the raw console output to master_run_{timestamp}.log."""
    log_path = os.path.join(target_dir, f"master_run_{timestamp_str}.log")
    with open(log_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(raw_content)
    return log_path


def write_dead_code_log(target_dir: str, timestamp_str: str, raw_content: str) -> str:
    """Writes the raw dead code audit console output to dead_code_{timestamp}.log."""
    log_path = os.path.join(target_dir, f"dead_code_{timestamp_str}.log")
    with open(log_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(raw_content)
    return log_path


def generate_dead_code_report(
    target_dir: str,
    timestamp_str: str,
    dead_code_result: Any,
) -> str:
    """Generates a dedicated dead_code_{timestamp}.md forensic report."""
    md_path = os.path.join(target_dir, f"dead_code_{timestamp_str}.md")
    status_badge = "🟢 **PASS**" if dead_code_result.total_findings == 0 else "⚠️ **FINDINGS DETECTED**"
    date_display = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    lines = [
        "# Bit-Logger Dead Code & Unreachable Logic Audit Report",
        "",
        f"> **Generated:** `{date_display}` | **Run ID:** `dead_code_{timestamp_str}`  ",
        f"> **Overall Status:** {status_badge}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Overall Result** | {status_badge} |",
        f"| **Total Source Files Scanned** | `{dead_code_result.total_files_scanned}` |",
        f"| **Total Dead Code Findings** | `{dead_code_result.total_findings}` |",
        "",
        "---",
        "",
        "## 2. Detected Unreachable Logic & Dead Code",
        "",
    ]

    if dead_code_result.findings:
        lines.extend([
            "| # | File | Line | Entity / Type | Details |",
            "|---|---|---|---|---|",
        ])
        for idx, finding in enumerate(dead_code_result.findings, start=1):
            lines.append(
                f"| {idx} | `{finding.rel_path}` | `{finding.line_number}` | `{finding.entity_name} ({finding.finding_type})` | {finding.details} |"
            )
        lines.append("")

        lines.extend([
            "### 🔍 Detailed Code Snippets",
            "",
        ])
        for idx, finding in enumerate(dead_code_result.findings, start=1):
            lines.extend([
                f"#### Finding #{idx}: `{finding.entity_name}` in `{finding.rel_path}:{finding.line_number}`",
                f"- **Finding Type:** `{finding.finding_type}`",
                f"- **Description:** {finding.details}",
                "",
            ])
            try:
                from test_helper_scripts.snippet_extractor import get_surrounding_code_snippet
                snippet = get_surrounding_code_snippet(finding.file_path, finding.line_number, context_lines=4)
                if snippet:
                    lines.extend([
                        "```python",
                        snippet,
                        "```",
                        "",
                    ])
            except Exception:
                pass
    else:
        lines.append("✅ **Zero unreachable statements or dead code detected across all audited source files.**\n")

    lines.extend([
        "---",
        "",
        "## 3. Logs & Artifacts",
        "",
        f"- **Raw Execution Log:** [`dead_code_{timestamp_str}.log`](./dead_code_{timestamp_str}.log)",
        f"- **Audit Report:** [`dead_code_{timestamp_str}.md`](./dead_code_{timestamp_str}.md)",
        "",
    ])

    with open(md_path, "w", encoding="utf-8", errors="replace") as f:
        f.write("\n".join(lines))

    return md_path


def generate_markdown_report(
    logs_dir: str,
    timestamp_str: str,
    profile_name: str,
    exit_code: int,
    loc_records: Optional[tuple] = None,
    import_result: Optional[Any] = None,
    mojibake_summary: Optional[Any] = None,
    dead_code_result: Optional[Any] = None,
    test_summary: Optional[Any] = None,
    failed_test_records: Optional[List[Any]] = None,
    timeout_seconds: float = 60.0,
    max_loc: int = 100,
) -> str:
    """Generates comprehensive, formatted master_run_{timestamp}.md forensic report."""
    md_path = os.path.join(logs_dir, f"master_run_{timestamp_str}.md")
    status_badge = "🟢 **PASS**" if exit_code == 0 else "🔴 **FAIL**"
    date_display = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    lines = [
        f"# Bit-Logger Forensic Test & Audit Report",
        f"",
        f"> **Generated:** `{date_display}` | **Run ID:** `master_run_{timestamp_str}`  ",
        f"> **Test Profile:** `{profile_name.upper()}` | **Overall Status:** {status_badge}",
        f"",
        f"---",
        f"",
        f"## 1. Executive Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| **Overall Result** | {status_badge} |",
        f"| **Active Profile** | `{profile_name}` |",
        f"| **Timeout Budget** | `{timeout_seconds}s` per suite |",
        f"| **Max LOC Threshold** | `{max_loc} LOC` |",
    ]

    if test_summary:
        lines.extend([
            f"| **Discovered Suites** | `{test_summary.total_discovered_suites}` |",
            f"| **Completed Suites** | `{test_summary.completed_suites}` |",
            f"| **Total Tests Executed** | `{test_summary.total_executed_tests}` |",
            f"| **Tests Passed** | `🟢 {test_summary.passed_tests}` |",
            f"| **Tests Failed** | `🔴 {test_summary.failed_tests}` |",
            f"| **Tests Skipped** | `🟡 {test_summary.skipped_tests}` |",
            f"| **Accounting Invariants** | `{'✅ Satisfied' if test_summary.invariants_satisfied else '❌ Broken'}` |",
        ])

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 2. Architecture & Modularity LOC Audit (Anti-God-File)",
        f"",
    ])

    if loc_records:
        all_files, oversized = loc_records
        lines.extend([
            f"- **Total Scanned Files:** `{len(all_files)}`",
            f"- **Files Within Limit (<= {max_loc} LOC):** `{len(all_files) - len(oversized)}`",
            f"- **Files Exceeding Limit (> {max_loc} LOC):** `{len(oversized)}`",
            f"",
        ])
        if oversized:
            lines.extend([
                f"### ⚠️ Decoupling Needed (Oversized Files)",
                f"",
                f"| LOC | Code Lines | Comments | Location | Action Required |",
                f"|---|---|---|---|---|",
            ])
            for rec in oversized:
                lines.append(
                    f"| **{rec.total_loc}** | {rec.code_lines} | {rec.comment_lines} | `{rec.rel_path}` | Modularize / Decompose |"
                )
            lines.append("")
        else:
            lines.append("✅ **All audited files satisfy the strict modularity limit.**\n")
    else:
        lines.append("*LOC audit not included in this profile.*\n")

    lines.extend([
        f"---",
        f"",
        f"## 3. Test Import Integrity & Coverage Audit",
        f"",
    ])

    if import_result:
        lines.extend([
            f"- **Total Python Files:** `{import_result.total_files}`",
            f"- **Total Source Modules:** `{import_result.total_source_files}`",
            f"- **Total Test Files:** `{import_result.total_test_files}`",
            f"- **Stale / Dangling Imports:** `{import_result.stale_imports_count}`",
            f"- **Untested Source Modules:** `{len(import_result.untested_source_files)}`",
            f"",
        ])
        if import_result.stale_import_records:
            lines.extend([
                f"### ❌ Stale / Broken Imports in Tests",
                f"",
                f"| Test File | Imported Module | Diagnosis |",
                f"|---|---|---|",
            ])
            for s in import_result.stale_import_records:
                lines.append(f"| `{s.test_file}` | `{s.imported_module}` | {s.reason} |")
            lines.append("")
        if import_result.untested_source_files:
            lines.extend([
                f"### ⚠️ Untested Modules (Strict Touch Rule Alert)",
                f"",
            ])
            for u in import_result.untested_source_files:
                lines.append(f"- ❓ `{u}` — *Missing matching test in `tests/`*")
            lines.append("")
    else:
        lines.append("*Import audit not included in this profile.*\n")

    lines.extend([
        f"---",
        f"",
        f"## 4. Text Corruption & Mojibake Audit",
        f"",
    ])

    if mojibake_summary:
        lines.extend([
            f"- **Total Files Scanned:** `{mojibake_summary.total_files_scanned}`",
            f"- **Corrupted Files Detected:** `{mojibake_summary.corrupted_files_count}`",
            f"- **Total Corrupted Lines:** `{mojibake_summary.total_corruptions_found}`",
            f"",
        ])
        if mojibake_summary.corrupted_records:
            lines.extend([
                f"### ⚠️ Corrupted Files Detected",
                f"",
                f"| File | Line | Snippet | Matched Signature |",
                f"|---|---|---|---|",
            ])
            for cr in mojibake_summary.corrupted_records:
                for f in cr.findings:
                    sig_list = ", ".join(f.matches.keys())
                    clean_content = f.line_content.replace("|", "\\|")[:60]
                    lines.append(f"| `{cr.rel_path}` | `{f.line_number}` | `{clean_content}` | `{sig_list}` |")
            lines.append("")
        else:
            lines.append("✅ **Zero text corruption or mojibake patterns detected.**\n")
    else:
        lines.append("*Mojibake audit not included in this profile.*\n")

    lines.extend([
        f"---",
        f"",
        f"## 5. Dead Code & Unreachable Logic Audit",
        f"",
    ])

    if dead_code_result:
        lines.extend([
            f"- **Total Source Files Scanned:** `{dead_code_result.total_files_scanned}`",
            f"- **Dead Code Findings:** `{dead_code_result.total_findings}`",
            f"",
        ])
        if dead_code_result.findings:
            lines.extend([
                f"### ⚠️ Dead / Unreachable Code Detected",
                f"",
                f"| File | Line | Entity / Type | Details |",
                f"|---|---|---|---|",
            ])
            for df in dead_code_result.findings:
                lines.append(f"| `{df.rel_path}` | `{df.line_number}` | `{df.entity_name} ({df.finding_type})` | {df.details} |")
            lines.append("")
        else:
            lines.append("✅ **No dead or unreachable code detected in source files.**\n")
    else:
        lines.append("*Dead code audit not included in this profile.*\n")

    lines.extend([
        f"---",
        f"",
        f"## 6. Forensic Test Execution & Detailed Failure Diagnostics",
        f"",
    ])

    if test_summary:
        if failed_test_records:
            lines.extend([
                f"### 🚨 Failure Summary Table",
                f"",
                f"| # | Classification | Suite File | Test Function | Line | Root Error |",
                f"|---|---|---|---|---|---|",
            ])
            for idx, fail in enumerate(failed_test_records, start=1):
                err_preview = (fail.error or "Assertion failed").splitlines()[0][:60].replace("|", "\\|")
                line_str = str(fail.line_number) if fail.line_number else "N/A"
                rel_suite = os.path.basename(fail.file_path)
                lines.append(
                    f"| {idx} | `{fail.classification.value.upper()}` | `{rel_suite}` | `{fail.test_name}` | `{line_str}` | `{err_preview}` |"
                )
            lines.append("")

            lines.extend([
                f"### 🔍 In-Depth Diagnostic Traces & Source Snippets",
                f"",
            ])

            for idx, fail in enumerate(failed_test_records, start=1):
                lines.extend([
                    f"#### ❌ Failure #{idx}: `{fail.test_name}`",
                    f"- **Suite File:** `{fail.file_path}`",
                    f"- **Classification:** `{fail.classification.value.upper()}`",
                    f"- **Failing Line:** `{fail.line_number or 'Not identified in traceback'}`",
                    f"- **Exit Code:** `{fail.process_exit_code if fail.process_exit_code is not None else 'N/A'}`",
                    f"",
                ])

                if fail.code_snippet:
                    lines.extend([
                        f"##### 📝 Source Code Context (Target Line Marked with `>>`):",
                        f"```python",
                        fail.code_snippet,
                        f"```",
                        f"",
                    ])

                if fail.error:
                    clean_err = "\n".join(fail.error.strip().splitlines()[:30])
                    lines.extend([
                        f"##### 📋 Error Traceback:",
                        f"```text",
                        clean_err,
                        f"```",
                        f"",
                    ])
        else:
            lines.append("✅ **All test suites passed cleanly within timeout budget.**\n")
    else:
        lines.append("*Test runner was not executed in this profile.*\n")

    lines.extend([
        f"---",
        f"",
        f"## 7. Logs & Raw Output Location",
        f"",
        f"- **Raw Execution Log:** [`master_run_{timestamp_str}.log`](./master_run_{timestamp_str}.log)",
        f"- **Audit Report:** [`master_run_{timestamp_str}.md`](./master_run_{timestamp_str}.md)",
        f"",
    ])

    with open(md_path, "w", encoding="utf-8", errors="replace") as f:
        f.write("\n".join(lines))

    return md_path
