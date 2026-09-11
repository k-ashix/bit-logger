"""
Unit Tests: Diagnostic Pattern Classifier
File: tests/unit/test_helper_scripts/test_classifier.py
"""

import pytest
from test_helper_scripts.classifier import DiagnosticClassifier


def test_compiler_error_detection_syntax():
    """Verifies that syntax errors in output are classified as compiler errors."""
    stderr = [
        "  File \"test_syntax.py\", line 12",
        "    def invalid_func(",
        "                    ^",
        "SyntaxError: '(' was never closed",
    ]
    stdout = []
    has_err = DiagnosticClassifier.has_affirmative_compiler_error("test_syntax.py", stderr, stdout)
    assert has_err is True


def test_compiler_error_detection_import():
    """Verifies that missing module imports are classified as compiler/import errors."""
    stderr = [
        "ImportError: cannot import name 'UnknownDetector' from 'src.detectors'",
    ]
    stdout = []
    has_err = DiagnosticClassifier.has_affirmative_compiler_error("test_detectors.py", stderr, stdout)
    assert has_err is True


def test_unhandled_crash_detection():
    """Verifies that memory errors or recursion crashes are classified as test crashes."""
    stderr = [
        "RecursionError: maximum recursion depth exceeded while calling a Python object",
    ]
    stdout = []
    has_crash = DiagnosticClassifier.has_unhandled_crash(stderr, stdout)
    assert has_crash is True


def test_clean_output_no_false_positives():
    """Verifies that standard passing output does not trigger false positive diagnostics."""
    stderr = []
    stdout = ["test_pass.py::test_ok PASSED [100%]"]
    assert DiagnosticClassifier.has_affirmative_compiler_error("test_pass.py", stderr, stdout) is False
    assert DiagnosticClassifier.has_unhandled_crash(stderr, stdout) is False
