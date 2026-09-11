"""
Unit Tests: Text Corruption & Mojibake Auditor
File: tests/unit/test_helper_scripts/test_mojibake.py
"""

import os
import tempfile
import pytest
from test_helper_scripts.parse_mojibake import (
    scan_file_for_mojibake,
    run_mojibake_audit,
    MOJIBAKE_SIGNATURES,
)


def test_scan_file_clean():
    """Verifies that clean text with standard ASCII and valid UTF-8 produces no findings."""
    clean_text = "Bit-Logger: Tracking Bitcoin transactions and P2P telemetry.\nStandard clean file."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as f:
        f.write(clean_text)
        temp_path = f.name

    try:
        record = scan_file_for_mojibake(temp_path, "clean_test.py")
        assert record is None
    finally:
        os.remove(temp_path)


def test_scan_file_detects_corrupted_characters():
    """Verifies that known mojibake signatures (corrupted quotes, dashes) are flagged."""
    corrupted_text = "This is a broken quote: â€˜Helloâ€™ and an em-dash â€” corrupted."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(corrupted_text)
        temp_path = f.name

    try:
        record = scan_file_for_mojibake(temp_path, "corrupt_test.txt")
        assert record is not None
        assert len(record.findings) == 1
        finding = record.findings[0]
        assert finding.line_number == 1
        assert "â€˜" in finding.matches
        assert "â€”" in finding.matches
    finally:
        os.remove(temp_path)
