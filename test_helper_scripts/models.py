"""
Bit-Logger Forensic Test Suite Models & Diagnostic Enums
Inspired by evidence-based test accounting and deterministic machine event streaming.
Module: test_helper_scripts/models.py
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


class SuiteLifecycle(str, Enum):
    """Execution state for each discovered test suite."""
    DISCOVERED = "discovered"
    STARTED = "started"
    COMPLETED = "completed"


class ValidationClassification(str, Enum):
    """Evidence-based classification of test suite outcomes."""
    PASS = "pass"
    TEST_FAILURE = "testFailure"
    COMPILE_ERROR = "compileError"
    TEST_CRASH = "testCrash"
    TIMEOUT = "timeout"
    RUNNER_FAILURE = "runnerFailure"
    INFRASTRUCTURE_FAILURE = "infrastructureFailure"
    NOT_EXECUTED = "notExecuted"
    SKIPPED = "skipped"


class DiagnosticLevel(str, Enum):
    """Severity level for validator internal diagnostics."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidatorDiagnostic:
    """Structured record of validator anomalies, warnings, or stream events."""
    level: DiagnosticLevel
    code: str
    message: str
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        detail_str = f" ({self.details})" if self.details else ""
        return f"[{self.code}] {self.level.value.upper()}: {self.message}{detail_str}"


@dataclass
class TestItemInfo:
    """Information about a specific test case within a suite."""
    test_id: int
    name: str
    is_success: bool
    is_skip: bool = False
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class FailedTestRecord:
    """Structured record of a failing test case or runner failure for reporting."""
    file_index: int
    file_path: str
    test_name: str
    classification: ValidationClassification
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    process_exit_code: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SuiteAccountingRecord:
    """Detailed accounting state for a single test suite."""
    suite_id: int
    path: str
    lifecycle: SuiteLifecycle = SuiteLifecycle.DISCOVERED
    classification: ValidationClassification = ValidationClassification.NOT_EXECUTED
    tests: List[TestItemInfo] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active_start_time: Optional[datetime] = None


@dataclass
class ValidatorAccountingSummary:
    """Mathematical accounting summary for the validator run."""
    total_discovered_suites: int
    completed_suites: int
    interrupted_suites: int
    not_executed_suites: int
    total_executed_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    invariants_satisfied: bool
    invariant_failure_reason: Optional[str] = None

    @classmethod
    def compute(cls, suites: List[SuiteAccountingRecord]) -> "ValidatorAccountingSummary":
        completed = sum(1 for s in suites if s.lifecycle == SuiteLifecycle.COMPLETED)
        interrupted = sum(1 for s in suites if s.lifecycle == SuiteLifecycle.STARTED)
        not_executed = sum(1 for s in suites if s.lifecycle == SuiteLifecycle.DISCOVERED)

        total_tests = sum(len(s.tests) for s in suites)
        passed = sum(s.passed_count for s in suites)
        failed = sum(s.failed_count for s in suites)
        skipped = sum(s.skipped_count for s in suites)

        total_suites = len(suites)
        suites_sum_check = (completed + interrupted + not_executed) == total_suites
        completed_test_cases = passed + failed + skipped
        tests_sum_check = completed_test_cases == total_tests

        satisfied = suites_sum_check and tests_sum_check
        reason = None
        if not suites_sum_check:
            reason = (
                f"Suite total mismatch: discovered ({total_suites}) != "
                f"completed ({completed}) + interrupted ({interrupted}) + notExecuted ({not_executed})"
            )
        elif not tests_sum_check:
            reason = (
                f"Test total mismatch: completed test cases ({completed_test_cases}) != "
                f"total recorded tests ({total_tests})"
            )

        return cls(
            total_discovered_suites=total_suites,
            completed_suites=completed,
            interrupted_suites=interrupted,
            not_executed_suites=not_executed,
            total_executed_tests=total_tests,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            invariants_satisfied=satisfied,
            invariant_failure_reason=reason,
        )
