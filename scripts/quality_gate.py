"""Run repository lint and non-UI pytest quality gates."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> int:
    """Run an internally constructed command and return its exit code."""

    print(f"> {' '.join(command)}", flush=True)

    # All command arguments are constructed internally from sys.executable
    # and fixed module names. shell=False prevents shell interpretation.
    result = subprocess.run(  # noqa: S603
        command,
        check=False,
        shell=False,
    )

    return result.returncode


def test_files_exist() -> bool:
    """Return whether pytest test files currently exist."""

    tests_directory = Path("tests")

    return tests_directory.is_dir() and any(
        tests_directory.rglob("test_*.py")
    )


def main() -> int:
    """Run Ruff and non-UI pytest tests."""

    ruff_exit_code = run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            ".",
        ]
    )

    if ruff_exit_code != 0:
        print("Quality gate failed: Ruff reported errors.")
        return 1

    if not test_files_exist():
        print(
            "No test files exist yet; pytest gate skipped during scaffold stage."
        )
        return 0

    pytest_exit_code = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-m",
            "not ui",
        ]
    )

    if pytest_exit_code != 0:
        print("Quality gate failed: non-UI pytest tests failed.")
        return 1

    print("quality gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())