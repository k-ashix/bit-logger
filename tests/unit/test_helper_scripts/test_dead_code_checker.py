"""
Unit Tests: Dead Code Checker
File: tests/unit/test_helper_scripts/test_dead_code_checker.py
"""

import tempfile
import os
import pytest
from test_helper_scripts.dead_code_checker import (
    scan_file_for_dead_code,
    run_dead_code_audit,
    format_dead_code_report_str,
    DeadCodeAuditResult,
    DeadCodeFinding,
)


def test_scan_file_no_dead_code():
    """Verifies that clean reachable code has zero findings."""
    clean_code = """
def calculate_fee(amount):
    if amount > 100:
        return amount * 0.01
    return 1.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(clean_code)
        temp_path = f.name

    try:
        findings = scan_file_for_dead_code(temp_path, "clean_module.py")
        assert len(findings) == 0
    finally:
        os.remove(temp_path)


def test_scan_file_unreachable_after_return():
    """Verifies that statements after a return in the same block are flagged as unreachable."""
    unreachable_code = """
def process_tx(txid):
    return txid
    print("This line is unreachable dead code")
    x = 10
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(unreachable_code)
        temp_path = f.name

    try:
        findings = scan_file_for_dead_code(temp_path, "dead_module.py")
        assert len(findings) == 2
        assert findings[0].finding_type == "UNREACHABLE_CODE"
        assert findings[0].line_number == 4
    finally:
        os.remove(temp_path)


def test_format_dead_code_report_str():
    """Verifies string formatting for clean and violation audit results."""
    clean_res = DeadCodeAuditResult(total_files_scanned=2, total_findings=0)
    clean_str = format_dead_code_report_str(clean_res)
    assert "[PASS]" in clean_str
    assert "No unreachable statements" in clean_str

    finding = DeadCodeFinding(
        file_path="foo.py",
        rel_path="foo.py",
        line_number=10,
        entity_name="Pass",
        finding_type="UNREACHABLE_CODE",
        details="Unreachable code after return",
    )
    warn_res = DeadCodeAuditResult(total_files_scanned=1, total_findings=1, findings=[finding])
    warn_str = format_dead_code_report_str(warn_res)
    assert "[WARN]" in warn_str
    assert "DEAD CODE DETECTED" in warn_str
    assert "foo.py" in warn_str
