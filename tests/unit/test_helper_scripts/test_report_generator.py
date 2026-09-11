"""
Unit Tests: Forensic Report & Log Generator
File: tests/unit/test_helper_scripts/test_report_generator.py
"""

import os
import tempfile
import pytest
from test_helper_scripts.report_generator import (
    get_timestamp_str,
    ensure_logs_dir,
    ensure_run_dir,
    write_log_file,
    write_dead_code_log,
    generate_markdown_report,
    generate_dead_code_report,
)
from test_helper_scripts.dead_code_checker import DeadCodeAuditResult, DeadCodeFinding


def test_get_timestamp_str_format():
    """Verifies timestamp string follows YYYYMMDD_HH_MM_AM/PM format (12-hr IST, no seconds)."""
    ts = get_timestamp_str()
    assert len(ts) == 17
    assert "_" in ts
    assert ("_AM" in ts or "_PM" in ts)


def test_ensure_run_dir():
    """Verifies hierarchical date and time run folder creation with AM/PM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir, ts, date_dir = ensure_run_dir(tmpdir, "20260911_04_55_PM")
        assert os.path.exists(date_dir)
        assert os.path.basename(date_dir) == "run_2026_09_11"
        assert os.path.exists(run_dir)
        assert os.path.basename(run_dir) == "run_04_55_PM"
        assert os.path.dirname(run_dir) == date_dir


def test_write_log_file_and_markdown_report():
    """Verifies creation and content of both timestamped log and markdown report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ts = "20260911_04_55_PM"
        raw_log = "[>>] BIT-LOGGER FORENSIC TEST MASTER ORCHESTRATOR\nTest completed."

        log_path = write_log_file(tmpdir, ts, raw_log)
        assert os.path.exists(log_path)
        assert os.path.basename(log_path) == f"master_run_{ts}.log"

        md_path = generate_markdown_report(
            logs_dir=tmpdir,
            timestamp_str=ts,
            profile_name="full",
            exit_code=0,
            timeout_seconds=60.0,
            max_loc=100,
        )
        assert os.path.exists(md_path)
        assert os.path.basename(md_path) == f"master_run_{ts}.md"

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Bit-Logger Forensic Test & Audit Report" in content
        assert "master_run_20260911_04_55_PM" in content
        assert "PASS" in content


def test_write_dead_code_log_and_report():
    """Verifies dedicated dead code log and markdown report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ts = "20260911_04_55_PM"
        raw_log = "[DEAD CODE] Clean run."

        log_path = write_dead_code_log(tmpdir, ts, raw_log)
        assert os.path.exists(log_path)
        assert os.path.basename(log_path) == f"dead_code_{ts}.log"

        result = DeadCodeAuditResult(total_files_scanned=5, total_findings=0)
        md_path = generate_dead_code_report(tmpdir, ts, result)
        assert os.path.exists(md_path)
        assert os.path.basename(md_path) == f"dead_code_{ts}.md"

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Bit-Logger Dead Code & Unreachable Logic Audit Report" in content
        assert "PASS" in content
