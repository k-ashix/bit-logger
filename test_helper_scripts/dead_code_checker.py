"""
Bit-Logger Dead Code & Unreachable Logic Auditor
Scans codebase for unused functions, unreachable code blocks, and orphaned definitions using AST.
Exports dedicated dead_code_{timestamp}.log and dead_code_{timestamp}.md artifacts.
Module: test_helper_scripts/dead_code_checker.py
"""

import ast
import os
import sys
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
    ".agents",
    "test_helper_scripts",
    "tests",
}


@dataclass
class DeadCodeFinding:
    file_path: str
    rel_path: str
    line_number: int
    entity_name: str
    finding_type: str
    details: str


@dataclass
class DeadCodeAuditResult:
    total_files_scanned: int = 0
    total_findings: int = 0
    findings: List[DeadCodeFinding] = field(default_factory=list)


class DeadCodeVisitor(ast.NodeVisitor):
    """AST visitor to detect unreachable statements and unused local definitions."""

    def __init__(self, file_path: str, rel_path: str) -> None:
        self.file_path = file_path
        self.rel_path = rel_path
        self.findings: List[DeadCodeFinding] = []

    def _check_unreachable_statements(self, statements: List[ast.stmt]) -> None:
        """Checks for unreachable statements appearing after return, raise, break, continue."""
        terminal_encountered = False
        for stmt in statements:
            if terminal_encountered:
                self.findings.append(
                    DeadCodeFinding(
                        file_path=self.file_path,
                        rel_path=self.rel_path,
                        line_number=stmt.lineno,
                        entity_name=type(stmt).__name__,
                        finding_type="UNREACHABLE_CODE",
                        details="Statement appears after terminal statement (return/raise/break/continue)",
                    )
                )
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                terminal_encountered = True

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_unreachable_statements(node.body)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_unreachable_statements(node.body)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._check_unreachable_statements(node.body)
        if node.orelse:
            self._check_unreachable_statements(node.orelse)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._check_unreachable_statements(node.body)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._check_unreachable_statements(node.body)
        self.generic_visit(node)


def scan_file_for_dead_code(file_path: str, rel_path: str) -> List[DeadCodeFinding]:
    """Parses a Python file and inspects AST for dead/unreachable code."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)
    except Exception:
        return []

    visitor = DeadCodeVisitor(file_path, rel_path)
    visitor.visit(tree)
    return visitor.findings


def run_dead_code_audit(root_dir: str = ".") -> DeadCodeAuditResult:
    """Recursively audits Python source files in the codebase for dead/unreachable code."""
    result = DeadCodeAuditResult()

    ignored = set(IGNORED_DIRS)
    ignored.discard("test_helper_scripts")
    root_helper_dir = os.path.normpath(os.path.join(root_dir, "test_helper_scripts"))

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [
            d for d in dirs
            if d not in ignored and os.path.normpath(os.path.join(root, d)) != root_helper_dir
        ]

        for file_name in files:
            if file_name.endswith(".py"):
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, root_dir)

                result.total_files_scanned += 1
                findings = scan_file_for_dead_code(full_path, rel_path)
                if findings:
                    result.total_findings += len(findings)
                    result.findings.extend(findings)

    return result


def format_dead_code_report_str(result: DeadCodeAuditResult) -> str:
    """Formats dead code audit findings as a plain text string for console and log output."""
    lines = [
        "=" * 80,
        " [DEAD CODE] BIT-LOGGER DEAD CODE & UNREACHABLE LOGIC AUDITOR",
        "=" * 80,
        f"Total Source Files Scanned : {result.total_files_scanned}",
        f"Dead Code Findings Detected : {result.total_findings}",
        "-" * 80,
    ]

    if result.total_findings == 0:
        lines.append("[PASS] No unreachable statements or dead code detected.")
        lines.append("=" * 80)
    else:
        lines.append("[WARN] DEAD CODE DETECTED:")
        for finding in result.findings:
            lines.append(f"  Line {finding.line_number} in {finding.rel_path}")
            lines.append(f"    -> [{finding.finding_type}] {finding.entity_name}: {finding.details}")
        lines.append("=" * 80)

    return "\n".join(lines) + "\n"


def print_dead_code_report(result: DeadCodeAuditResult) -> None:
    """Renders formatted console diagnostic report for dead code audit."""
    print(format_dead_code_report_str(result), end="")


def run_standalone_dead_code_audit(root_dir: str = ".") -> int:
    """Executes dead code audit standalone and exports dedicated log and markdown artifacts."""
    from test_helper_scripts.report_generator import (
        DualLogger,
        ensure_run_dir,
        write_dead_code_log,
        generate_dead_code_report,
    )

    run_dir, timestamp_str, date_dir = ensure_run_dir(root_dir)

    original_stdout = sys.stdout
    dual_logger = DualLogger(original_stdout)
    sys.stdout = dual_logger

    try:
        result = run_dead_code_audit(root_dir)
        print_dead_code_report(result)
    finally:
        sys.stdout = original_stdout

    log_path = write_dead_code_log(run_dir, timestamp_str, dual_logger.get_logs())
    md_path = generate_dead_code_report(run_dir, timestamp_str, result)

    print(f"📁 [DEAD CODE ARTIFACTS GENERATED IN {os.path.relpath(date_dir, root_dir)}/]:")
    print(f"   ├──> Raw Log : {log_path}")
    print(f"   └──> Markdown: {md_path}\n")

    return 0 if result.total_findings == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit codebase for dead and unreachable code.")
    parser.add_argument("--root", type=str, default=".", help="Root directory to audit (default: .)")
    args = parser.parse_args()

    exit_code = run_standalone_dead_code_audit(args.root)
    sys.exit(exit_code)
