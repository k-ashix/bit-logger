"""
Unit Tests: Forensic Snippet Extractor
File: tests/unit/test_helper_scripts/test_snippet_extractor.py
"""

import os
import tempfile
import pytest
from test_helper_scripts.snippet_extractor import (
    extract_failure_line_number,
    find_test_function_line,
    get_surrounding_code_snippet,
    extract_failure_context,
)


def test_extract_failure_line_number_pytest_format():
    """Verifies regex extraction from pytest style traceback."""
    err_text = "tests/unit/test_example.py:42: in test_something\nassert False"
    line_num = extract_failure_line_number("tests/unit/test_example.py", err_text)
    assert line_num == 42


def test_extract_failure_line_number_python_traceback():
    """Verifies regex extraction from standard python traceback."""
    err_text = '  File "tests/unit/test_foo.py", line 88, in test_run\n    raise ValueError()'
    line_num = extract_failure_line_number("tests/unit/test_foo.py", err_text)
    assert line_num == 88


def test_get_surrounding_code_snippet():
    """Verifies extraction of surrounding context with target line marker '>>'."""
    lines = [f"line_{i} = {i}\n" for i in range(1, 20)]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.writelines(lines)
        temp_path = f.name

    try:
        snippet = get_surrounding_code_snippet(temp_path, target_line=10, context_lines=2)
        assert snippet is not None
        assert "10 >> line_10 = 10" in snippet
        assert " 8    line_8 = 8" in snippet
        assert "12    line_12 = 12" in snippet
    finally:
        os.remove(temp_path)
