"""Reject staged secrets, local databases, and protected files."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

ALLOWED_ENV_FILES = {
    ".env.example",
    ".env.sample",
    ".env.template",
}

BLOCKED_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}

BLOCKED_FILENAMES = {
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}

SECRET_PATTERNS = (
    (
        "private key",
        re.compile(r"-----BEGIN [A-Z ]{0,40}PRIVATE KEY-----"),
    ),
    (
        "GitHub classic token",
        re.compile(r"\bghp_[A-Za-z0-9]{20,255}\b"),
    ),
    (
        "GitHub fine-grained token",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,255}\b"),
    ),
    (
        "AWS access-key identifier",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "secret-key-shaped value",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,255}\b"),
    ),
)

MAX_SCANNED_BYTES = 1_000_000


def run_git(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run a trusted Git command and capture its byte output."""

    git_executable = shutil.which("git")

    if git_executable is None:
        raise RuntimeError("Git executable was not found on PATH.")

    # The executable is resolved with shutil.which, arguments are internally
    # constructed, and shell=False is used. No command string is interpreted.
    return subprocess.run(  # noqa: S603
        [git_executable, *command],
        capture_output=True,
        check=False,
        shell=False,
    )


def staged_files() -> list[str]:
    """Return added, copied, modified, or renamed staged files."""

    result = run_git(
        [
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
            "-z",
        ]
    )

    if result.returncode != 0:
        print(
            "Unable to inspect staged files.",
            file=sys.stderr,
        )
        return []

    return [
        item.decode("utf-8", errors="replace")
        for item in result.stdout.split(b"\0")
        if item
    ]


def is_protected_path(path: str) -> bool:
    """Return whether a path must never be committed."""

    normalized = path.replace("\\", "/")
    lowercase_path = normalized.lower()
    pure_path = PurePosixPath(normalized)
    filename = pure_path.name.lower()

    if filename in ALLOWED_ENV_FILES:
        return False

    if filename == ".env" or filename.startswith(".env."):
        return True

    if filename in BLOCKED_FILENAMES:
        return True

    if lowercase_path.startswith("instance/"):
        return True

    return pure_path.suffix.lower() in BLOCKED_SUFFIXES


def staged_content(path: str) -> str:
    """Return staged text, or an empty string for binary or large files."""

    result = run_git(["show", f":{path}"])

    if result.returncode != 0:
        return ""

    if len(result.stdout) > MAX_SCANNED_BYTES:
        return ""

    if b"\0" in result.stdout:
        return ""

    return result.stdout.decode("utf-8", errors="replace")


def main() -> int:
    """Run staged-path and staged-content security checks."""

    failures: list[str] = []

    for path in staged_files():
        if is_protected_path(path):
            failures.append(f"protected file is staged: {path}")
            continue

        content = staged_content(path)

        for secret_name, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                failures.append(
                    f"{secret_name} detected in staged file: {path}"
                )
                break

    if failures:
        print("PRE-COMMIT SECURITY GATE FAILED", file=sys.stderr)

        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

        print(
            "Remove the protected file or secret before committing.",
            file=sys.stderr,
        )
        return 1

    print("pre-commit security gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
