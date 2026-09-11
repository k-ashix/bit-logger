"""
Bit-Logger Forensic Test Runner & Diagnostic Validator
Executes test suites with strict 60s per-suite timeout, evidence-based failure classification,
and mathematical invariant verification.
Module: test_helper_scripts/test_runner.py
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from test_helper_scripts.models import (
    SuiteLifecycle,
    ValidationClassification,
    DiagnosticLevel,
    ValidatorDiagnostic,
    TestItemInfo,
    FailedTestRecord,
    SuiteAccountingRecord,
    ValidatorAccountingSummary,
)
from test_helper_scripts.classifier import DiagnosticClassifier


class ForensicTestRunner:
    """
    Core deterministic test execution engine and accounting processor.
    Guarantees strict per-suite execution timeout (default 60s) to prevent hangs.
    """

    def __init__(self, timeout_seconds: float = 60.0, root_dir: str = ".") -> None:
        self.timeout_seconds = timeout_seconds
        self.root_dir = root_dir
        self.suites_map: Dict[int, SuiteAccountingRecord] = {}
        self.diagnostics: List[ValidatorDiagnostic] = []
        self.failed_test_records: List[FailedTestRecord] = []
        self._first_root_failure: Optional[FailedTestRecord] = None

    @property
    def first_root_failure(self) -> Optional[FailedTestRecord]:
        return self._first_root_failure

    def add_diagnostic(self, level: DiagnosticLevel, code: str, message: str, details: Optional[str] = None) -> None:
        diag = ValidatorDiagnostic(level=level, code=code, message=message, details=details)
        self.diagnostics.append(diag)

    def _set_first_root_failure(self, record: FailedTestRecord) -> None:
        if self._first_root_failure is None:
            self._first_root_failure = record

    def discover_test_suites(self) -> List[str]:
        """Discovers all test suite files matching test_*.py or *_test.py in the repository."""
        test_files: List[str] = []
        ignored = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".agents"}
        root_helper_dir = os.path.normpath(os.path.join(self.root_dir, "test_helper_scripts"))

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [
                d for d in dirs
                if d not in ignored and os.path.normpath(os.path.join(root, d)) != root_helper_dir
            ]
            for f in sorted(files):
                if f == "test_master.py":
                    continue
                if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                    test_files.append(os.path.normpath(os.path.join(root, f)))

        for idx, path in enumerate(test_files, start=1):
            self.suites_map[idx] = SuiteAccountingRecord(
                suite_id=idx,
                path=path,
                lifecycle=SuiteLifecycle.DISCOVERED,
                classification=ValidationClassification.NOT_EXECUTED,
            )

        self.add_diagnostic(
            DiagnosticLevel.INFO,
            "SUITES_DISCOVERED",
            f"Discovered {len(test_files)} test suites in workspace",
        )
        return test_files

    def run_suite(self, suite_id: int) -> SuiteAccountingRecord:
        """
        Executes a single test suite with hard timeout enforcement (60s).
        Captures stdout and stderr, classifies outcomes with evidence.
        """
        record = self.suites_map[suite_id]
        record.lifecycle = SuiteLifecycle.STARTED
        record.start_time = datetime.now()
        record.active_start_time = record.start_time

        # Check if pytest is available, else fallback to zero-dependency native runner
        has_pytest = False
        try:
            import pytest
            has_pytest = True
        except ImportError:
            has_pytest = False

        if has_pytest:
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short", record.path]
        else:
            native_runner = os.path.join(os.path.dirname(__file__), "native_suite_runner.py")
            cmd = [sys.executable, native_runner, record.path]

        stdout_lines: List[str] = []
        stderr_lines: List[str] = []
        exit_code: Optional[int] = None
        is_timeout = False

        start_time_monotonic = time.perf_counter()

        try:
            # Subprocess execution with hard timeout
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.root_dir,
            )

            try:
                out, err = proc.communicate(timeout=self.timeout_seconds)
                exit_code = proc.returncode
                stdout_lines = out.splitlines() if out else []
                stderr_lines = err.splitlines() if err else []
            except subprocess.TimeoutExpired:
                is_timeout = True
                proc.kill()
                out, err = proc.communicate()
                stdout_lines = out.splitlines() if out else []
                stderr_lines = err.splitlines() if err else []
                stderr_lines.append(f"FATAL: Test suite exceeded timeout limit of {self.timeout_seconds}s and was killed.")

        except Exception as e:
            record.lifecycle = SuiteLifecycle.COMPLETED
            record.classification = ValidationClassification.RUNNER_FAILURE
            fail_rec = FailedTestRecord(
                file_index=len(self.failed_test_records) + 1,
                file_path=record.path,
                test_name="Runner Exception",
                error=str(e),
                classification=ValidationClassification.RUNNER_FAILURE,
            )
            self.failed_test_records.append(fail_rec)
            self._set_first_root_failure(fail_rec)
            return record

        elapsed_ms = (time.perf_counter() - start_time_monotonic) * 1000.0
        record.end_time = datetime.now()

        # Handle Timeout
        if is_timeout:
            record.lifecycle = SuiteLifecycle.COMPLETED
            record.classification = ValidationClassification.TIMEOUT
            record.failed_count += 1
            fail_rec = FailedTestRecord(
                file_index=len(self.failed_test_records) + 1,
                file_path=record.path,
                test_name=f"[TIMEOUT] Exceeded {self.timeout_seconds}s execution budget",
                error=f"Test process killed after {elapsed_ms:.1f}ms (threshold: {self.timeout_seconds}s)",
                classification=ValidationClassification.TIMEOUT,
                process_exit_code=exit_code,
            )
            self.failed_test_records.append(fail_rec)
            self._set_first_root_failure(fail_rec)
            return record

        # Parse test results from stdout
        self._parse_pytest_output(record, stdout_lines, stderr_lines, exit_code, elapsed_ms)
        return record

    def _parse_pytest_output(
        self,
        record: SuiteAccountingRecord,
        stdout_lines: List[str],
        stderr_lines: List[str],
        exit_code: int,
        elapsed_ms: float,
    ) -> None:
        """Parses stdout/stderr and classifies the suite outcome."""
        test_case_id = 1

        for line in stdout_lines:
            stripped = line.strip()
            if "::" in stripped:
                parts = stripped.split()
                test_name = parts[0]
                status = parts[-1] if len(parts) > 1 else ""

                if "PASSED" in status:
                    record.passed_count += 1
                    record.tests.append(
                        TestItemInfo(
                            test_id=test_case_id,
                            name=test_name,
                            is_success=True,
                            duration_ms=elapsed_ms,
                        )
                    )
                    test_case_id += 1
                elif "FAILED" in status:
                    record.failed_count += 1
                    record.tests.append(
                        TestItemInfo(
                            test_id=test_case_id,
                            name=test_name,
                            is_success=False,
                            error=f"Assertion or test failure in {test_name}",
                            duration_ms=elapsed_ms,
                        )
                    )
                    fail_rec = FailedTestRecord(
                        file_index=len(self.failed_test_records) + 1,
                        file_path=record.path,
                        test_name=test_name,
                        error=stripped,
                        classification=ValidationClassification.TEST_FAILURE,
                        process_exit_code=exit_code,
                    )
                    self.failed_test_records.append(fail_rec)
                    self._set_first_root_failure(fail_rec)
                    test_case_id += 1
                elif "SKIPPED" in status:
                    record.skipped_count += 1
                    record.tests.append(
                        TestItemInfo(
                            test_id=test_case_id,
                            name=test_name,
                            is_success=True,
                            is_skip=True,
                            duration_ms=elapsed_ms,
                        )
                    )
                    test_case_id += 1

        record.lifecycle = SuiteLifecycle.COMPLETED

        if exit_code == 0:
            record.classification = (
                ValidationClassification.PASS if record.failed_count == 0 else ValidationClassification.TEST_FAILURE
            )
        else:
            if DiagnosticClassifier.has_affirmative_compiler_error(record.path, stderr_lines, stdout_lines):
                record.classification = ValidationClassification.COMPILE_ERROR
                err_msg = "\n".join((stderr_lines + stdout_lines)[:25])
                fail_rec = FailedTestRecord(
                    file_index=len(self.failed_test_records) + 1,
                    file_path=record.path,
                    test_name="[COMPILE / SYNTAX / IMPORT ERROR]",
                    error=err_msg,
                    classification=ValidationClassification.COMPILE_ERROR,
                    process_exit_code=exit_code,
                )
                self.failed_test_records.append(fail_rec)
                self._set_first_root_failure(fail_rec)
            elif DiagnosticClassifier.has_unhandled_crash(stderr_lines, stdout_lines):
                record.classification = ValidationClassification.TEST_CRASH
                err_msg = "\n".join((stderr_lines + stdout_lines)[:25])
                fail_rec = FailedTestRecord(
                    file_index=len(self.failed_test_records) + 1,
                    file_path=record.path,
                    test_name="[TEST PROCESS CRASH]",
                    error=err_msg,
                    classification=ValidationClassification.TEST_CRASH,
                    process_exit_code=exit_code,
                )
                self.failed_test_records.append(fail_rec)
                self._set_first_root_failure(fail_rec)
            else:
                record.classification = (
                    ValidationClassification.TEST_FAILURE
                    if record.failed_count > 0
                    else ValidationClassification.RUNNER_FAILURE
                )

    def run_all(self) -> ValidatorAccountingSummary:
        """Discovers and executes all test suites, calculating final mathematical summary."""
        self.discover_test_suites()
        for suite_id in sorted(self.suites_map.keys()):
            self.run_suite(suite_id)

        return ValidatorAccountingSummary.compute(list(self.suites_map.values()))

    def print_summary(self, summary: ValidatorAccountingSummary) -> None:
        """Renders evidence-based forensic test summary report."""
        print("=" * 80)
        print(" [ACCOUNTING] BIT-LOGGER FORENSIC TEST VALIDATOR ACCOUNTING SUMMARY")
        print(f" Execution Timeout Budget: {self.timeout_seconds}s per suite")
        print("=" * 80)
        print(f"Discovered Suites : {summary.total_discovered_suites}")
        print(f"Completed Suites  : {summary.completed_suites}")
        print(f"Interrupted Suites: {summary.interrupted_suites}")
        print(f"Not Executed      : {summary.not_executed_suites}")
        print("-" * 80)
        print(f"Total Tests Executed: {summary.total_executed_tests}")
        print(f"Passed Tests        : {summary.passed_tests}")
        print(f"Failed Tests        : {summary.failed_tests}")
        print(f"Skipped Tests       : {summary.skipped_tests}")
        print("-" * 80)
        print(f"Accounting Invariants Satisfied: {'[PASS] YES' if summary.invariants_satisfied else '[FAIL] NO'}")
        if not summary.invariants_satisfied:
            print(f"   └──> Invariant Failure Reason: {summary.invariant_failure_reason}")

        print("=" * 80)

        if self.failed_test_records:
            print("[ROOT FAILURES] DETECTED TEST FAILURES:")
            for rec in self.failed_test_records:
                print(f" [{rec.classification.value.upper()}] Suite: {rec.file_path}")
                print(f"  Test : {rec.test_name}")
                if rec.error:
                    first_err_line = rec.error.strip().splitlines()[0]
                    print(f"  Error: {first_err_line}")
                print("-" * 80)


if __name__ == "__main__":
    runner = ForensicTestRunner(timeout_seconds=60.0)
    summary = runner.run_all()
    runner.print_summary(summary)
    sys.exit(0 if (summary.failed_tests == 0 and summary.invariants_satisfied) else 1)
