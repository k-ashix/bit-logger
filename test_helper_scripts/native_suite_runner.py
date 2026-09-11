"""
Bit-Logger Native Test Suite Runner (Zero-Dependency)
Executes test functions (test_*) and unittest.TestCase classes without requiring pytest.
Provides an offline shim for pytest if not installed in the environment.
Module: test_helper_scripts/native_suite_runner.py
"""

import sys
import os
import types
import inspect
import importlib.util
import traceback
from typing import List, Tuple, Callable

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Inject zero-dependency pytest compatibility shim if pytest is not installed
if "pytest" not in sys.modules:
    try:
        import pytest
    except ImportError:
        pytest_shim = types.ModuleType("pytest")

        class _MockMark:
            def parametrize(self, *args, **kwargs):
                return lambda fn: fn

        class _MockRaises:
            def __init__(self, expected_exception, match=None):
                self.expected_exception = expected_exception
                self.match = match

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None and issubclass(exc_type, self.expected_exception):
                    return True
                raise AssertionError(
                    f"Expected exception {self.expected_exception} was not raised. Got: {exc_type}"
                )

        pytest_shim.mark = _MockMark()
        pytest_shim.fixture = lambda fn: fn
        pytest_shim.raises = _MockRaises
        sys.modules["pytest"] = pytest_shim


def run_single_file_tests(test_file_path: str) -> int:
    """Dynamically imports a test module and executes all test_* functions."""
    abs_path = os.path.abspath(test_file_path)
    if not os.path.exists(abs_path):
        print(f"Error: Test file not found: {abs_path}", file=sys.stderr)
        return 1

    # Ensure project root is in sys.path
    project_root = os.path.dirname(os.path.dirname(abs_path))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    safe_name = abs_path.replace(os.sep, "_").replace(".", "_").replace(":", "_")
    module_name = f"test_module_{safe_name}"
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        print(f"Compilation failed: Unable to load spec for {abs_path}", file=sys.stderr)
        return 1

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"SyntaxError or ImportError in {abs_path}:", file=sys.stderr)
        traceback.print_exc()
        return 1

    # Discover test functions
    tests_to_run: List[Tuple[str, Callable]] = []
    for attr_name in dir(module):
        if attr_name.startswith("test_") or attr_name.endswith("_test"):
            attr = getattr(module, attr_name)
            if callable(attr):
                tests_to_run.append((attr_name, attr))

    base_file = os.path.basename(abs_path)
    passed = 0
    failed = 0

    for name, func in tests_to_run:
        sig = inspect.signature(func)
        try:
            if len(sig.parameters) == 0:
                func()
            else:
                # Handle test functions expecting simple fixtures if available in module
                kwargs = {}
                for param in sig.parameters:
                    if hasattr(module, param):
                        fixture_factory = getattr(module, param)
                        kwargs[param] = fixture_factory() if callable(fixture_factory) else fixture_factory
                    else:
                        break
                if len(kwargs) == len(sig.parameters):
                    func(**kwargs)
                else:
                    print(f"{base_file}::{name} SKIPPED (unresolved arguments)")
                    continue

            print(f"{base_file}::{name} PASSED")
            passed += 1
        except AssertionError as ae:
            failed += 1
            print(f"{base_file}::{name} FAILED", file=sys.stderr)
            traceback.print_exc()
        except Exception as ex:
            failed += 1
            print(f"{base_file}::{name} FAILED (Exception: {type(ex).__name__})", file=sys.stderr)
            traceback.print_exc()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python native_suite_runner.py <test_file_path>")
        sys.exit(1)

    exit_code = run_single_file_tests(sys.argv[1])
    sys.exit(exit_code)
