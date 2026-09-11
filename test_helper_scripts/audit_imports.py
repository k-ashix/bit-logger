"""
Bit-Logger Test Import & Coverage Auditor
Audits whether source files are tested, and detects stale or broken imports in test suites.
Module: test_helper_scripts/audit_imports.py
"""

import os
import ast
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
}


@dataclass
class StaleImportRecord:
    test_file: str
    imported_module: str
    reason: str


@dataclass
class ImportAuditResult:
    total_files: int = 0
    total_source_files: int = 0
    total_test_files: int = 0
    stale_imports_count: int = 0
    stale_import_records: List[StaleImportRecord] = field(default_factory=list)
    untested_source_files: List[str] = field(default_factory=list)
    tested_source_files: List[str] = field(default_factory=list)


def extract_python_imports(file_path: str) -> List[str]:
    """Extracts top-level imported module names from a Python source file using AST."""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def run_test_import_audit(root_dir: str = ".") -> ImportAuditResult:
    """
    Scans source and test files to audit test imports and mapping integrity.
    """
    result = ImportAuditResult()
    source_files: List[str] = []
    test_files: List[str] = []

    # 1. Discover all Python files
    ignored = set(IGNORED_DIRS)
    ignored.discard("test_helper_scripts")
    root_helper_dir = os.path.normpath(os.path.join(root_dir, "test_helper_scripts"))

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [
            d for d in dirs
            if d not in ignored and os.path.normpath(os.path.join(root, d)) != root_helper_dir
        ]
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.normpath(os.path.join(root, f))
                result.total_files += 1

                # Classify test file vs source file
                if "test" in f.lower() or os.sep + "tests" + os.sep in full_path:
                    test_files.append(full_path)
                else:
                    source_files.append(full_path)

    result.total_source_files = len(source_files)
    result.total_test_files = len(test_files)

    # 2. Check imports in each test file for broken or stale imports
    for t_file in test_files:
        imported_modules = extract_python_imports(t_file)
        for mod in imported_modules:
            if mod.startswith("src.") or mod == "src":
                mod_rel_path = mod.replace(".", os.sep)
                expected_py = os.path.normpath(os.path.join(root_dir, f"{mod_rel_path}.py"))
                expected_pkg = os.path.normpath(os.path.join(root_dir, mod_rel_path, "__init__.py"))

                if not os.path.exists(expected_py) and not os.path.exists(expected_pkg):
                    result.stale_imports_count += 1
                    result.stale_import_records.append(
                        StaleImportRecord(
                            test_file=t_file,
                            imported_module=mod,
                            reason=f"Target module '{mod}' not found on filesystem",
                        )
                    )

    # 3. Check which source files in src/ lack a corresponding test file
    src_base_names = set()
    for s_file in source_files:
        base = os.path.basename(s_file)
        if base in ("__init__.py", "main.py", "app.py", "conftest.py"):
            continue
        stem = os.path.splitext(base)[0]
        src_base_names.add((stem, s_file))

    test_stems = {os.path.splitext(os.path.basename(t))[0].replace("test_", "").replace("_test", "") for t in test_files}

    for stem, s_file in src_base_names:
        if stem in test_stems or f"test_{stem}" in test_stems:
            result.tested_source_files.append(s_file)
        else:
            result.untested_source_files.append(s_file)

    return result


def print_import_audit_report(result: ImportAuditResult) -> None:
    """Prints a structured console diagnostic report."""
    print("=" * 80)
    print(" [AUDIT] BIT-LOGGER TEST IMPORT & COVERAGE AUDITOR")
    print("=" * 80)
    print(f"Total Python Files Scanned : {result.total_files}")
    print(f"Total Source Modules        : {result.total_source_files}")
    print(f"Total Test Files            : {result.total_test_files}")
    print(f"Stale / Broken Test Imports : {result.stale_imports_count}")
    print(f"Untested Source Modules     : {len(result.untested_source_files)}")
    print("-" * 80)

    if result.stale_imports_count > 0:
        print("[FAIL] STALE / BROKEN IMPORTS DETECTED IN TEST SUITES:")
        for rec in result.stale_import_records:
            print(f"   [!] File  : {rec.test_file}")
            print(f"       Import: {rec.imported_module}")
            print(f"       Reason: {rec.reason}")
        print("-" * 80)
    else:
        print("[PASS] No stale or dangling test imports found.")

    if result.untested_source_files:
        print("[WARN] UNTESTED SOURCE MODULES (VIOLATES STRICT TOUCH RULE):")
        for s_file in result.untested_source_files:
            print(f"   [?] Missing Unit Test: {s_file}")
            print(f"       └──> Create tests/unit/.../test_{os.path.basename(s_file)}")
        print("-" * 80)
    else:
        print("[PASS] All discovered source modules have matching test coverage.")

    print("=" * 80)


if __name__ == "__main__":
    res = run_test_import_audit(".")
    print_import_audit_report(res)
    sys.exit(0 if res.stale_imports_count == 0 else 1)
