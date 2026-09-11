"""
Bit-Logger Master Test & Forensic Verification Orchestrator
Coordinates:
  1. Architecture & Modularity LOC Audit (<= 100 LOC limit)
  2. Test Import Integrity & Coverage Audit (Stale imports & Untested modules)
  3. Text Corruption & Mojibake Audit (UTF-8 corruptions)
  4. Dead Code & Unreachable Logic Audit (Unreachable blocks, AST inspection)
  5. Parallel Forensic Test Runner (1 to 9 worker threads, default 3)
  6. Deep Failure Diagnostics & Source Code Snippets in reports
  7. Dual timestamped logging to test_helper_scripts/logs/:
     - master_run_{date_time}.log
     - master_run_{date_time}.md
Module: test_helper_scripts/test_master.py
"""

import sys
import os
import argparse
from typing import Optional, List, Tuple, Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from test_helper_scripts.audit_loc import run_architecture_loc_audit, print_audit_report
from test_helper_scripts.audit_imports import run_test_import_audit, print_import_audit_report
from test_helper_scripts.parse_mojibake import run_mojibake_audit, print_mojibake_report
from test_helper_scripts.dead_code_checker import (
    run_dead_code_audit,
    print_dead_code_report,
    format_dead_code_report_str,
)
from test_helper_scripts.parallel_runner import (
    ParallelForensicRunner,
    DEFAULT_WORKERS,
    MIN_WORKERS,
    MAX_WORKERS,
    clamp_workers,
)
from test_helper_scripts.report_generator import (
    DualLogger,
    get_timestamp_str,
    ensure_logs_dir,
    ensure_run_dir,
    write_log_file,
    write_dead_code_log,
    generate_markdown_report,
    generate_dead_code_report,
)


PROFILES = {
    "full": {
        "description": "Complete run: LOC audit, Imports audit, Mojibake audit, Dead code audit, and Tests (60s timeout)",
        "loc": True,
        "imports": True,
        "mojibake": True,
        "dead_code": True,
        "tests": True,
        "timeout": 60.0,
        "strict": False,
    },
    "quick": {
        "description": "Fast smoke verification with 15s timeout budget",
        "loc": True,
        "imports": True,
        "mojibake": False,
        "dead_code": False,
        "tests": True,
        "timeout": 15.0,
        "strict": False,
    },
    "audit": {
        "description": "Static architectural and encoding audits only (No test execution)",
        "loc": True,
        "imports": True,
        "mojibake": True,
        "dead_code": True,
        "tests": False,
        "timeout": 60.0,
        "strict": False,
    },
    "tests": {
        "description": "Executes all test suites with 60s timeout (No static audits)",
        "loc": False,
        "imports": False,
        "mojibake": False,
        "dead_code": False,
        "tests": True,
        "timeout": 60.0,
        "strict": False,
    },
    "strict": {
        "description": "Zero-tolerance run: fails on ANY warning, LOC violation, dead code, or untested module",
        "loc": True,
        "imports": True,
        "mojibake": True,
        "dead_code": True,
        "tests": True,
        "timeout": 60.0,
        "strict": True,
    },
}


def run_master_suite(
    root_dir: str = ".",
    profile_name: str = "full",
    workers: int = DEFAULT_WORKERS,
    timeout_seconds: float = 60.0,
    max_loc: int = 100,
    run_loc_audit: bool = True,
    run_import_audit: bool = True,
    run_mojibake_check: bool = True,
    run_dead_code_check: bool = True,
    run_tests: bool = True,
    strict_mode: bool = False,
) -> int:
    """Runs requested audits and test suites, generating dual timestamped logs in a dedicated run directory."""
    run_dir, timestamp_str, date_dir = ensure_run_dir(root_dir)
    safe_workers = clamp_workers(workers)

    original_stdout = sys.stdout
    dual_logger = DualLogger(original_stdout)
    sys.stdout = dual_logger

    exit_code = 0
    loc_records: Optional[Tuple[Any, Any]] = None
    import_res: Optional[Any] = None
    mojibake_summary: Optional[Any] = None
    dead_code_res: Optional[Any] = None
    test_summary: Optional[Any] = None
    failed_test_records: List[Any] = []

    try:
        print("\n" + "=" * 80)
        print(" [>>] BIT-LOGGER FORENSIC TEST MASTER ORCHESTRATOR")
        print(f" Run ID         : master_run_{timestamp_str}")
        print(f" Active Profile : {profile_name.upper()}")
        print(f" Worker Threads : {safe_workers} (Bounded: {MIN_WORKERS} to {MAX_WORKERS})")
        print(f" Root Directory : {os.path.abspath(root_dir)}")
        print(f" Timeout Budget : {timeout_seconds}s per suite | Max LOC: {max_loc}")
        print(f" Strict Mode    : {'ENABLED (Zero-tolerance)' if strict_mode else 'DISABLED'}")
        print("=" * 80 + "\n")

        # 1. Architecture Modularity LOC Audit
        if run_loc_audit:
            all_files, violations = run_architecture_loc_audit(root_dir=root_dir, max_loc=max_loc)
            loc_records = (all_files, violations)
            print_audit_report(all_files, violations, max_loc=max_loc)
            if len(violations) > 0:
                print(f"[!] Warning: {len(violations)} files exceed {max_loc} LOC threshold.\n")
                if strict_mode:
                    exit_code = 1

        # 2. Test Import & Coverage Audit
        if run_import_audit:
            import_res = run_test_import_audit(root_dir=root_dir)
            print_import_audit_report(import_res)
            if import_res.stale_imports_count > 0:
                exit_code = 1
            if strict_mode and import_res.untested_source_files:
                exit_code = 1

        # 3. Text Corruption & Mojibake Audit
        if run_mojibake_check:
            mojibake_summary = run_mojibake_audit(root_dir=root_dir)
            print_mojibake_report(mojibake_summary)
            if mojibake_summary.corrupted_files_count > 0:
                exit_code = 1

        # 4. Dead Code & Unreachable Logic Audit
        if run_dead_code_check:
            dead_code_res = run_dead_code_audit(root_dir=root_dir)
            print_dead_code_report(dead_code_res)
            if strict_mode and dead_code_res.total_findings > 0:
                exit_code = 1

        # 5. Multi-Threaded Test Runner with Timeout
        if run_tests:
            parallel_runner = ParallelForensicRunner(
                workers=safe_workers,
                timeout_seconds=timeout_seconds,
                root_dir=root_dir,
            )
            test_summary = parallel_runner.run_all()
            parallel_runner.print_summary(test_summary)
            failed_test_records = parallel_runner.failed_test_records

            if test_summary.failed_tests > 0 or not test_summary.invariants_satisfied:
                exit_code = 1

        print("\n" + "=" * 80)
        if exit_code == 0:
            print("[+] OVERALL STATUS: ALL FORENSIC CHECKS & TESTS PASSED SUCCESSFULLY.")
        else:
            print("[-] OVERALL STATUS: FAILURES OR STRICT VIOLATIONS DETECTED.")
        print("=" * 80 + "\n")

    finally:
        sys.stdout = original_stdout

    # Export master timestamped raw console logs and Markdown report into dedicated run directory
    log_file_path = write_log_file(run_dir, timestamp_str, dual_logger.get_logs())
    md_file_path = generate_markdown_report(
        logs_dir=run_dir,
        timestamp_str=timestamp_str,
        profile_name=profile_name,
        exit_code=exit_code,
        loc_records=loc_records,
        import_result=import_res,
        mojibake_summary=mojibake_summary,
        dead_code_result=dead_code_res,
        test_summary=test_summary,
        failed_test_records=failed_test_records,
        timeout_seconds=timeout_seconds,
        max_loc=max_loc,
    )

    dead_code_log_path: Optional[str] = None
    dead_code_md_path: Optional[str] = None
    if run_dead_code_check:
        if dead_code_res is None:
            dead_code_res = run_dead_code_audit(root_dir=root_dir)
        dead_code_log_content = format_dead_code_report_str(dead_code_res)
        dead_code_log_path = write_dead_code_log(run_dir, timestamp_str, dead_code_log_content)
        dead_code_md_path = generate_dead_code_report(run_dir, timestamp_str, dead_code_res)

    print(f"📁 [RUN ARTIFACTS GENERATED IN {os.path.relpath(date_dir, root_dir)}/]:")
    print(f"   ├──> Master Log      : {log_file_path}")
    print(f"   ├──> Master Report   : {md_file_path}")
    if dead_code_log_path and dead_code_md_path:
        print(f"   ├──> Dead Code Log   : {dead_code_log_path}")
        print(f"   └──> Dead Code Report: {dead_code_md_path}\n")
    else:
        print()

    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(description="Bit-Logger Master Test & Forensic Verification Script")
    parser.add_argument(
        "--profile",
        type=str,
        choices=list(PROFILES.keys()),
        default=None,
        help="Select pre-configured test profile: full, quick, audit, tests, strict",
    )
    parser.add_argument("--all", action="store_true", help="Run all audits and test suites (equivalent to --profile full)")
    parser.add_argument("--audit-loc", action="store_true", help="Run only architecture LOC audit")
    parser.add_argument("--audit-imports", action="store_true", help="Run only test import and coverage audit")
    parser.add_argument("--mojibake", action="store_true", help="Run only text corruption / mojibake audit")
    parser.add_argument("--dead-code", action="store_true", help="Run only dead code / unreachable logic audit")
    parser.add_argument("--tests", action="store_true", help="Run only test execution suite")
    parser.add_argument("--timeout", type=float, default=None, help="Per-suite timeout in seconds (default: 60s)")
    parser.add_argument("--max-loc", type=int, default=100, help="Maximum allowed LOC per file (default: 100)")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode (warnings cause failure)")
    parser.add_argument("--workers", "--threads", "-j", type=int, default=DEFAULT_WORKERS, help="Parallel worker threads (1-9, default: 3)")
    parser.add_argument("--root", type=str, default=".", help="Root directory to scan (default: .)")

    # Shorthand concurrency flags: --1, --2, --3, ... --9
    for i in range(1, 10):
        parser.add_argument(f"--{i}", dest=f"thread_flag_{i}", action="store_true", help=f"Run with {i} parallel worker threads")

    args = parser.parse_args()

    # Determine thread count (shorthand flag overrides --workers default)
    selected_workers = args.workers
    for i in range(1, 10):
        if getattr(args, f"thread_flag_{i}", False):
            selected_workers = i
            break

    # Determine profile settings
    profile_key = args.profile or "full"
    profile_cfg = PROFILES[profile_key]

    timeout = args.timeout if args.timeout is not None else profile_cfg["timeout"]
    strict = args.strict or profile_cfg["strict"]

    # Check for individual override flags
    individual_flags = [args.audit_loc, args.audit_imports, args.mojibake, args.dead_code, args.tests]
    if any(individual_flags):
        do_loc = args.audit_loc
        do_imports = args.audit_imports
        do_mojibake = args.mojibake
        do_dead_code = args.dead_code
        do_tests = args.tests
        effective_profile = "custom"
    else:
        do_loc = profile_cfg["loc"]
        do_imports = profile_cfg["imports"]
        do_mojibake = profile_cfg["mojibake"]
        do_dead_code = profile_cfg["dead_code"]
        do_tests = profile_cfg["tests"]
        effective_profile = profile_key

    rc = run_master_suite(
        root_dir=args.root,
        profile_name=effective_profile,
        workers=selected_workers,
        timeout_seconds=timeout,
        max_loc=args.max_loc,
        run_loc_audit=do_loc,
        run_import_audit=do_imports,
        run_mojibake_check=do_mojibake,
        run_dead_code_check=do_dead_code,
        run_tests=do_tests,
        strict_mode=strict,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
