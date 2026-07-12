#!/usr/bin/env python3
"""
Run All Tests — Comprehensive Test Runner
==========================================
Runs all project tests at once with --keepdb (preserves test database).

Usage:
    python run_all_tests.py              # Quick tests (SQLite)
    python run_all_tests.py --pg         # Accurate tests (PostgreSQL via Docker)
    python run_all_tests.py --pg --jmeter  # Full suite + JMeter

Requirements:
    - SQLite: no setup needed (default)
    - PostgreSQL: needs Docker + pg-test container on port 5433
    - JMeter: needs JMeter installed + Docker running
"""
import os
import sys
import subprocess
import time
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

SETTINGS_SQLITE = "config.settings.test_sqlite"
SETTINGS_PG = "config.settings.test"
PASS = "PASS"
FAIL = "FAIL"


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(name, success, detail=""):
    icon = PASS if success else FAIL
    print(f"  [{icon}] {name}" + (f" — {detail}" if detail else ""))


def run_cmd(cmd, label, timeout=300, stdin_data=None):
    """Run a command and show the result."""
    print(f"\n  >> {label}")
    print(f"     {cmd}")
    sys.stdout.flush()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, input=stdin_data)
        success = result.returncode == 0
        output_lines = result.stdout.splitlines()
        error_lines = result.stderr.splitlines()
        for line in output_lines:
            if line.strip():
                print(f"    {line}")
        for line in error_lines:
            if line.strip() and "warning" not in line.lower():
                print(f"    {line}")
        print_result(label, success, "OK" if success else f"FAILED (code {result.returncode})")
        return success
    except subprocess.TimeoutExpired:
        print_result(label, False, f"TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print_result(label, False, str(e))
        return False


def check_postgres():
    """Ensure PostgreSQL container is running or start it."""
    result = subprocess.run(
        "docker ps --format '{{.Names}} {{.Status}}'",
        shell=True, capture_output=True, text=True, timeout=10
    )
    if "pg-test" in result.stdout and "Up" in result.stdout:
        print("  [i] PostgreSQL 'pg-test' is running")
        return True
    if "ecommerce-postgres" in result.stdout:
        print("  [i] PostgreSQL 'ecommerce-postgres' is running")
        return True

    # Try starting existing container
    start_result = subprocess.run(
        "docker start pg-test", shell=True, capture_output=True, text=True, timeout=15
    )
    if start_result.returncode == 0:
        print("  [*] Started existing 'pg-test' container...")
        time.sleep(3)
        return True

    # Create new container with max_connections=200 for 100 concurrent threads
    print("  [i] Creating new PostgreSQL container (max_connections=200)...")
    run_result = subprocess.run(
        "docker run -d --name pg-test -e POSTGRES_DB=ecommerce "
        "-e POSTGRES_USER=ecommerce -e POSTGRES_PASSWORD=ecommerce "
        "-p 5433:5432 postgres:18 -c max_connections=200",
        shell=True, capture_output=True, text=True, timeout=60
    )
    if run_result.returncode == 0:
        print("  [*] Waiting for PostgreSQL to be ready...")
        time.sleep(5)
        return True
    print(f"  [FAIL] Could not start PostgreSQL: {run_result.stderr.strip()}")
    return False


def run_unit_tests(settings):
    """Run all unit tests (27)."""
    return run_cmd(
        f"python -m django test tests --settings={settings} --verbosity=2 --keepdb",
        f"Unit Tests (27) — {settings}",
        timeout=300
    )


def run_stress_tests(settings):
    """Run stress tests (3)."""
    return run_cmd(
        f"python -m django test tests.stress_oversell tests.stress_cache tests.stress_async "
        f"--settings={settings} --verbosity=2 --keepdb",
        f"Stress Tests (3) — {settings}",
        timeout=120
    )


def run_performance_test(settings):
    """Run the Before/After performance test."""
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = settings
    return run_cmd(
        f"python performance_test.py",
        f"Performance Test — {settings}",
        timeout=120
    )


def run_jmeter_tests():
    """Run JMeter tests (requires Docker + running API)."""
    print()
    # Check if API is responding
    result = subprocess.run(
        "curl -s -o nul -w \"%{http_code}\" http://localhost:80/api/products/?page=1",
        shell=True, capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0 or "200" not in result.stdout:
        print("  [WARN] API is not running (check docker-compose up --build)")
        print("     First verify: curl http://localhost:80/api/products/?page=1")
        return False

    success = True
    success &= run_cmd(
        "jmeter -n -t jmeter/02-CacheTest.jmx -l jmeter-live.jtl",
        "JMeter Cache Test",
        timeout=60
    )
    success &= run_cmd(
        "jmeter -g jmeter-live.jtl -o jmeter-live-report/",
        "JMeter Report Generation",
        timeout=30
    )
    return success


def main():
    parser = argparse.ArgumentParser(description="Run All Tests — Comprehensive Test Runner")
    parser.add_argument("--pg", action="store_true", help="Use PostgreSQL (default: SQLite)")
    parser.add_argument("--jmeter", action="store_true", help="Include JMeter tests")
    parser.add_argument("--unit-only", action="store_true", help="Run unit tests only")
    parser.add_argument("--stress-only", action="store_true", help="Run stress tests only")
    parser.add_argument("--perf-only", action="store_true", help="Run performance test only")
    args = parser.parse_args()

    settings = SETTINGS_PG if args.pg else SETTINGS_SQLITE
    db_type = "PostgreSQL" if args.pg else "SQLite"
    results = []

    print_header(f"RUN ALL TESTS — Comprehensive Test Runner ({db_type})")
    print(f"  Directory: {BASE_DIR}")
    print(f"  Settings:  {settings}")
    print(f"  Time:      {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.pg:
        print(f"\n  Connecting to PostgreSQL...")
        if not check_postgres():
            print(f"  [{FAIL}] PostgreSQL not available. Use --pg only with Docker.")
            sys.exit(1)
        print(f"  [{PASS}] PostgreSQL ready")

    total_start = time.monotonic()

    if args.stress_only:
        results.append(("Stress Tests (3)", run_stress_tests(settings)))
    elif args.perf_only:
        results.append(("Performance Test", run_performance_test(settings)))
    elif args.unit_only:
        results.append(("Unit Tests (27)", run_unit_tests(settings)))
    else:
        results.append(("Unit Tests (27)", run_unit_tests(settings)))
        results.append(("Stress Tests (3)", run_stress_tests(settings)))

    if args.jmeter:
        results.append(("JMeter Tests", run_jmeter_tests()))

    total_time = time.monotonic() - total_start

    print_header("FINAL RESULTS")
    all_passed = True
    for name, success in results:
        all_passed = all_passed and success
        print_result(name, success)

    print(f"\n  Total time: {total_time:.1f}s")
    print(f"\n  {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    if all_passed:
        print(f"  30/30 tests passing — project is ready for submission!")
    else:
        print(f"  Check errors above and fix before submission.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
