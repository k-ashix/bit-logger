"""
Bit-Logger Parallel Forensic Test Runner (Thread Pool)
Manages parallel test suite execution across worker threads with strict safety bounds,
thread-safe state synchronization, and per-suite 60s timeout enforcement.
Module: test_helper_scripts/parallel_runner.py
"""

import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any

from test_helper_scripts.models import (
    SuiteLifecycle,
    ValidationClassification,
    DiagnosticLevel,
    FailedTestRecord,
    SuiteAccountingRecord,
    ValidatorAccountingSummary,
)
from test_helper_scripts.test_runner import ForensicTestRunner
from test_helper_scripts.snippet_extractor import extract_failure_context

DEFAULT_WORKERS = 3
MIN_WORKERS = 1
MAX_WORKERS = 9


def clamp_workers(requested_workers: int) -> int:
    """Clamps requested worker threads safely between MIN_WORKERS (1) and MAX_WORKERS (9)."""
    if requested_workers < MIN_WORKERS:
        return MIN_WORKERS
    if requested_workers > MAX_WORKERS:
        return MAX_WORKERS
    return requested_workers


class ParallelForensicRunner:
    """
    Executes multiple test suites concurrently across a bounded thread pool (1 to 9 workers).
    Guarantees thread-safe accounting, isolated per-suite timeouts, and deep failure context extraction.
    """

    def __init__(
        self,
        workers: int = DEFAULT_WORKERS,
        timeout_seconds: float = 60.0,
        root_dir: str = ".",
    ) -> None:
        self.workers = clamp_workers(workers)
        self.timeout_seconds = timeout_seconds
        self.root_dir = root_dir

        self.runner = ForensicTestRunner(timeout_seconds=self.timeout_seconds, root_dir=self.root_dir)
        self._lock = threading.Lock()
        self.completed_count = 0
        self.total_count = 0

    def _execute_suite_thread_safe(self, suite_id: int) -> SuiteAccountingRecord:
        """Executes a suite in an isolated thread worker, extracting rich code context on failure."""
        record = self.runner.run_suite(suite_id)

        # Thread-safe result processing and context enrichment
        with self._lock:
            self.completed_count += 1
            progress_pct = (self.completed_count / max(1, self.total_count)) * 100.0
            status_tag = record.classification.value.upper()

            rel_path = os.path.relpath(record.path, self.root_dir)
            print(
                f" [{self.completed_count:02d}/{self.total_count:02d}] "
                f"({progress_pct:5.1f}%) [TH-{threading.get_ident() % 1000:03d}] "
                f"{status_tag:<12} | {rel_path}"
            )

            # Deep failure enrichment with code snippets
            for fail_rec in self.runner.failed_test_records:
                if fail_rec.file_path == record.path and fail_rec.code_snippet is None:
                    line_num, snippet = extract_failure_context(
                        file_path=fail_rec.file_path,
                        test_name=fail_rec.test_name,
                        error_text=fail_rec.error,
                        context_lines=5,
                    )
                    fail_rec.line_number = line_num
                    fail_rec.code_snippet = snippet

        return record

    def run_all(self) -> ValidatorAccountingSummary:
        """Discovers all test suites and coordinates parallel execution across bounded worker threads."""
        test_files = self.runner.discover_test_suites()
        self.total_count = len(test_files)
        self.completed_count = 0

        print("=" * 80)
        print(" 🧵  BIT-LOGGER MULTI-THREADED TEST RUNNER (PARALLEL EXECUTION)")
        print(f" Active Worker Threads : {self.workers} (Bounded: {MIN_WORKERS} to {MAX_WORKERS})")
        print(f" Total Suites Queued   : {self.total_count}")
        print(f" Hard Timeout per Suite: {self.timeout_seconds}s")
        print("=" * 80)

        if self.total_count == 0:
            print("[INFO] No test suites discovered in workspace.")
            return ValidatorAccountingSummary.compute([])

        suite_ids = sorted(self.runner.suites_map.keys())

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_suite = {
                executor.submit(self._execute_suite_thread_safe, s_id): s_id
                for s_id in suite_ids
            }
            for future in as_completed(future_to_suite):
                try:
                    future.result()
                except Exception as e:
                    s_id = future_to_suite[future]
                    with self._lock:
                        self.runner.add_diagnostic(
                            DiagnosticLevel.ERROR,
                            "WORKER_UNHANDLED_EXCEPTION",
                            f"Worker thread encountered unhandled exception for suite {s_id}: {str(e)}",
                        )

        summary = ValidatorAccountingSummary.compute(list(self.runner.suites_map.values()))
        return summary

    def print_summary(self, summary: ValidatorAccountingSummary) -> None:
        """Delegates summary rendering to the underlying forensic runner."""
        self.runner.print_summary(summary)

    @property
    def failed_test_records(self) -> List[FailedTestRecord]:
        return self.runner.failed_test_records
