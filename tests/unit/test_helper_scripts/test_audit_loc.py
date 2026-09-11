"""
Unit Tests: Architecture LOC Auditor
File: tests/unit/test_helper_scripts/test_audit_loc.py
"""

import os
import tempfile
import pytest
from test_helper_scripts.audit_loc import analyze_file_loc, run_architecture_loc_audit


def test_analyze_file_loc_within_threshold():
    """Verifies that a file under 100 LOC is correctly classified."""
    content = "import os\n\ndef hello():\n    # greeting\n    return 'world'\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        record = analyze_file_loc(temp_path, max_loc=100)
        assert record is not None
        assert record.total_loc == 5
        assert record.code_lines == 3
        assert record.comment_lines == 1
        assert record.blank_lines == 1
        assert record.exceeds_limit is False
    finally:
        os.remove(temp_path)


def test_analyze_file_loc_exceeds_threshold():
    """Verifies that a file over 100 LOC triggers the decoupling flag."""
    lines = [f"x_{i} = {i}\n" for i in range(120)]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.writelines(lines)
        temp_path = f.name

    try:
        record = analyze_file_loc(temp_path, max_loc=100)
        assert record is not None
        assert record.total_loc == 120
        assert record.exceeds_limit is True
    finally:
        os.remove(temp_path)
