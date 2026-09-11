"""
Bit-Logger Forensic Code Snippet & Failure Context Extractor
Extracts exact failing line numbers and surrounding source code context for forensic reporting.
Module: test_helper_scripts/snippet_extractor.py
"""

import os
import re
from typing import Optional, Tuple, List


def extract_failure_line_number(file_path: str, error_text: str) -> Optional[int]:
    """
    Parses traceback and error output to locate the line number where the failure occurred.
    """
    if not error_text:
        return None

    base_name = re.escape(os.path.basename(file_path))

    # Pattern 1: pytest style -> test_file.py:42: in test_function
    match = re.search(rf"{base_name}:(\d+):", error_text)
    if match:
        return int(match.group(1))

    # Pattern 2: standard python traceback -> File "...test_file.py", line 42, in test_function
    match = re.search(rf'{base_name}", line (\d+)', error_text)
    if match:
        return int(match.group(1))

    # Pattern 3: generic line number fallback
    match = re.search(r", line (\d+)", error_text)
    if match:
        return int(match.group(1))

    return None


def find_test_function_line(file_path: str, test_name: str) -> Optional[int]:
    """
    Searches the source file for the definition of the failing test function.
    """
    clean_test_name = test_name.split("::")[-1].split("[")[0].strip()
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                if re.search(rf"def\s+{re.escape(clean_test_name)}\s*\(", line):
                    return idx
    except Exception:
        return None

    return None


def get_surrounding_code_snippet(
    file_path: str,
    target_line: int,
    context_lines: int = 5,
) -> Optional[str]:
    """
    Reads the file and extracts a formatted window around the target line with line markers.
    """
    if not os.path.exists(file_path) or target_line <= 0:
        return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return None

    total_lines = len(lines)
    if target_line > total_lines:
        return None

    start = max(1, target_line - context_lines)
    end = min(total_lines, target_line + context_lines)

    snippet_lines: List[str] = []
    for line_num in range(start, end + 1):
        content = lines[line_num - 1].rstrip("\r\n")
        marker = ">>" if line_num == target_line else "  "
        snippet_lines.append(f"{line_num:4d} {marker} {content}")

    return "\n".join(snippet_lines)


def extract_failure_context(
    file_path: str,
    test_name: str,
    error_text: Optional[str],
    context_lines: int = 5,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Locates the failure line (from traceback or function definition) and extracts source snippet.
    Returns (line_number, formatted_code_snippet).
    """
    line_num = None
    if error_text:
        line_num = extract_failure_line_number(file_path, error_text)

    if line_num is None:
        line_num = find_test_function_line(file_path, test_name)

    snippet = None
    if line_num is not None:
        snippet = get_surrounding_code_snippet(file_path, line_num, context_lines=context_lines)

    return line_num, snippet
