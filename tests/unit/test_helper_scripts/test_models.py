"""
Unit Tests: Test Accounting Models & Invariants
File: tests/unit/test_helper_scripts/test_models.py
"""

import pytest
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


def test_validator_diagnostic_formatting():
    """Verifies string formatting of diagnostic messages."""
    diag = ValidatorDiagnostic(
        level=DiagnosticLevel.WARNING,
        code="SLOW_TEST",
        message="Test exceeded 5s threshold",
        details="test_peeling.py",
    )
    formatted = str(diag)
    assert "[SLOW_TEST] WARNING: Test exceeded 5s threshold (test_peeling.py)" in formatted


def test_validator_accounting_summary_invariants_satisfied():
    """Verifies that mathematical accounting invariants hold when suites and tests match."""
    suites = [
        SuiteAccountingRecord(
            suite_id=1,
            path="tests/unit/test_a.py",
            lifecycle=SuiteLifecycle.COMPLETED,
            classification=ValidationClassification.PASS,
            passed_count=2,
            failed_count=0,
            skipped_count=0,
            tests=[
                TestItemInfo(test_id=1, name="test_1", is_success=True),
                TestItemInfo(test_id=2, name="test_2", is_success=True),
            ],
        ),
        SuiteAccountingRecord(
            suite_id=2,
            path="tests/unit/test_b.py",
            lifecycle=SuiteLifecycle.COMPLETED,
            classification=ValidationClassification.TEST_FAILURE,
            passed_count=1,
            failed_count=1,
            skipped_count=0,
            tests=[
                TestItemInfo(test_id=3, name="test_3", is_success=True),
                TestItemInfo(test_id=4, name="test_4", is_success=False, error="AssertionError"),
            ],
        ),
    ]

    summary = ValidatorAccountingSummary.compute(suites)

    assert summary.total_discovered_suites == 2
    assert summary.completed_suites == 2
    assert summary.total_executed_tests == 4
    assert summary.passed_tests == 3
    assert summary.failed_tests == 1
    assert summary.invariants_satisfied is True
    assert summary.invariant_failure_reason is None


def test_validator_accounting_summary_invariants_mismatch():
    """Verifies that invariant failure is caught when counts do not balance."""
    suites = [
        SuiteAccountingRecord(
            suite_id=1,
            path="tests/unit/test_broken_math.py",
            lifecycle=SuiteLifecycle.COMPLETED,
            passed_count=5,  # Mismatch: claims 5 passed, but only 1 test registered
            tests=[TestItemInfo(test_id=1, name="test_single", is_success=True)],
        ),
    ]

    summary = ValidatorAccountingSummary.compute(suites)
    assert summary.invariants_satisfied is False
    assert "Test total mismatch" in summary.invariant_failure_reason
