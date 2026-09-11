"""
Unit Tests: Parallel Forensic Test Runner & Bounded Concurrency
File: tests/unit/test_helper_scripts/test_parallel_runner.py
"""

import pytest
from test_helper_scripts.parallel_runner import (
    clamp_workers,
    MIN_WORKERS,
    MAX_WORKERS,
    DEFAULT_WORKERS,
    ParallelForensicRunner,
)


def test_clamp_workers_boundaries():
    """Verifies that thread worker count is bounded strictly between 1 and 9."""
    assert clamp_workers(0) == MIN_WORKERS
    assert clamp_workers(-5) == MIN_WORKERS
    assert clamp_workers(1) == 1
    assert clamp_workers(3) == 3
    assert clamp_workers(9) == 9
    assert clamp_workers(10) == MAX_WORKERS
    assert clamp_workers(99) == MAX_WORKERS


def test_parallel_runner_initialization():
    """Verifies runner initialization with bounded threads and timeout."""
    runner = ParallelForensicRunner(workers=5, timeout_seconds=45.0)
    assert runner.workers == 5
    assert runner.timeout_seconds == 45.0
    assert runner.total_count == 0


def test_parallel_runner_clamped_init():
    """Verifies that out-of-range worker values are clamped at construction."""
    runner_high = ParallelForensicRunner(workers=20)
    assert runner_high.workers == MAX_WORKERS

    runner_low = ParallelForensicRunner(workers=-2)
    assert runner_low.workers == MIN_WORKERS
