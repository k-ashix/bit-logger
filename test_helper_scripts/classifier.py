"""
Bit-Logger Diagnostic Pattern Matcher & Failure Classifier
Module: test_helper_scripts/classifier.py
"""

import re
from typing import List


class DiagnosticClassifier:
    """Diagnostic pattern matcher for evidence-based failure classification."""

    COMPILER_PATTERNS = [
        re.compile(r"SyntaxError:", re.IGNORECASE),
        re.compile(r"IndentationError:", re.IGNORECASE),
        re.compile(r"TabError:", re.IGNORECASE),
        re.compile(r"ModuleNotFoundError:", re.IGNORECASE),
        re.compile(r"ImportError:", re.IGNORECASE),
        re.compile(r"Failed to import", re.IGNORECASE),
        re.compile(r"Compilation failed", re.IGNORECASE),
        re.compile(r"Error: (Could not find|Cannot find|Undefined)", re.IGNORECASE),
    ]

    CRASH_PATTERNS = [
        "RecursionError:",
        "MemoryError:",
        "SystemExit:",
        "KeyboardInterrupt",
        "Segmentation fault",
        "Process terminated with signal",
        "Fatal Python error:",
        "InternalError:",
    ]

    @classmethod
    def has_affirmative_compiler_error(
        cls,
        file_path: str,
        stderr_lines: List[str],
        stdout_lines: List[str],
    ) -> bool:
        """Detects if test runner failed due to compilation, syntax, or import failures."""
        import os
        file_name = os.path.basename(file_path)
        all_lines = stderr_lines + stdout_lines

        for line in all_lines:
            if file_name in line or "Error:" in line:
                for pattern in cls.COMPILER_PATTERNS:
                    if pattern.search(line):
                        return True
        return False

    @classmethod
    def has_unhandled_crash(
        cls,
        stderr_lines: List[str],
        stdout_lines: List[str],
    ) -> bool:
        """Detects if test process died from an unhandled interpreter crash or out-of-memory."""
        all_lines = stderr_lines + stdout_lines
        for line in all_lines:
            for crash_pattern in cls.CRASH_PATTERNS:
                if crash_pattern in line:
                    return True
        return False
