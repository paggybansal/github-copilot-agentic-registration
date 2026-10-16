# Verification — REG-1 User Registration

| Field | Value |
|---|---|
| Artifact | Verification |
| SDLC Step | 7. Verification |
| Source | `docs/01-requirements.md` (Approved), `docs/02-architecture.md` (Approved, Revision 1), `docs/04-impl-plan.md` (Approved), `docs/05-code-review.md` (Approved) |
| Author Role | Verifier (Copilot agent) |
| Commit | `7b8bed3e19c2eeb7eabfa6d8d1ae02a68559ba05` |
| Date | 2026-10-16 |
| Status | Approved |

## 1. Environment

```text
Python 3.14.2
OS: Microsoft Windows NT 10.0.26200.0
Chrome: 155.0.8059.40 (headless, local Selenium Manager-provisioned ChromeDriver)
pytest 9.1.1
```

Working tree note: one uncommitted, unrelated documentation edit exists (`docs/01-requirements.md` `Status: Draft → Approved`), already disclosed in `docs/05-code-review.md` (CR-1, deferred). It does not affect any file verified below.

## 2. Static Checks

```text
$ ruff check .
All checks passed!
```

Result: Pass.

```text
$ pip-audit
Name                                Skip Reason
----------------------------------- --------------------------------------------------------------------------------------------------
github-copilot-agentic-registration Dependency not found on PyPI and could not be audited: github-copilot-agentic-registration (0.1.0)
No known vulnerabilities found
```

Result: Pass — no known vulnerabilities in any auditable dependency; the local unpublished package is expectedly skipped.

## 3. pytest and Coverage

```text
$ python -m pytest -q
============================ 119 passed in 24.07s =============================
```

Result: Pass — 119/119 tests pass, including the 2 Selenium UI tests.

```text
$ python -m pytest --cov=src/registration_app --cov-report=term-missing -q
Name                                 Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------------------
src\registration_app\__init__.py         1      0      0      0   100%
src\registration_app\app.py             15      0      2      0   100%
src\registration_app\config.py          15      0      0      0   100%
src\registration_app\db.py              16      0      4      0   100%
src\registration_app\forms.py            8      0      0      0   100%
src\registration_app\repository.py      23      0      2      0   100%
src\registration_app\routes.py          51      0     12      0   100%
src\registration_app\security.py         6      0      0      0   100%
src\registration_app\validation.py      70      0     28      0   100%
--------------------------------------------------------------------------------
TOTAL                                  205      0     48      0   100%
============================ 119 passed in 24.52s =============================
```

Result: Pass — 100% line and branch coverage of `src/registration_app`, exceeding the NFR-5 target of ≥85%. No production line is uncovered.

## 4. Verification Matrix (V-1–V-15)

| ID | Scenario | Expected result | Actual result | Evidence | Verdict |
|---|---|---|---|---|---|
| V-1 | Registration page loads | GET `/register` returns HTTP 200 with Full Name, Email, Password, Confirm Password and a Register button | Confirmed | `tests/test_routes.py::test_register_get_returns_200_and_renders_form` PASSED | Pass |
| V-2 | Successful registration | Valid POST creates exactly one account and redirects (PRG) to the success page showing only "Registration successful" | Confirmed | `tests/test_routes.py::test_register_post_valid_data_creates_user_and_redirects`, `::test_register_post_redirect_followed_shows_success_message` PASSED | Pass |
| V-3 | Required fields | POST with missing fields returns HTTP 200, creates no account, shows field-specific messages, retains Full Name/Email | Confirmed | `tests/test_routes.py::test_register_post_missing_fields_rerenders_with_errors_and_retains_values` PASSED | Pass |
| V-4 | Invalid email | POST with a malformed email returns HTTP 200 with "Enter a valid email address" | Confirmed | `tests/test_routes.py::test_register_post_invalid_email_rerenders_with_error` PASSED | Pass |
| V-5 | Weak-password variants | POST violating length/uppercase/lowercase/digit rules is rejected with a clear message per rule | Confirmed | `tests/test_routes.py::test_register_post_weak_password_rerenders_with_error`; `tests/test_validation.py` (missing-uppercase/lowercase/number, below-8, above-128) all PASSED | Pass |
| V-6 | Password mismatch | POST with differing Password/Confirm Password shows "Passwords do not match" | Confirmed | `tests/test_routes.py::test_register_post_password_mismatch_rerenders_with_error` PASSED | Pass |
| V-7 | Duplicate email, including different casing | Second POST with an existing (or differently cased) normalized email shows "An account with this email already exists"; only one account exists | Confirmed | `tests/test_routes.py::test_register_post_duplicate_email_same_case_rejects_second_user`, `::test_register_post_duplicate_email_different_case_rejects_second_user`, `::test_register_post_duplicate_email_race_returns_duplicate_message` PASSED | Pass |
| V-8 | Password stored as a hash | Stored value differs from the submitted password and verifies via Werkzeug | Confirmed. Stored-hash method prefix observed: `scrypt:32768:8:1...` (full hash not published per evidence rules) | `tests/test_security.py::test_hash_password_returns_hash_different_from_plain_password`, `::test_verify_password_returns_true_for_correct_password` PASSED | Pass |
| V-9 | Submitted HTML/script cannot execute | An XSS-shaped Full Name is rendered as escaped text, not executed | Confirmed | `tests/test_routes.py::test_register_post_xss_shaped_full_name_escaped_in_rerendered_form`, `tests/test_templates.py::test_register_template_escapes_xss_shaped_full_name` PASSED | Pass |
| V-10 | Database error rolls back and returns the generic message | Simulated DB failure leaves no partial row, shows "Registration could not be completed. Please try again", no SQL/path/traceback exposed | Confirmed | `tests/test_routes.py::test_register_post_database_error_returns_generic_message`, `tests/test_security_edge_cases.py::test_register_database_failure_response_contains_only_generic_message` PASSED | Pass |
| V-11 | CSRF rejects a missing/invalid token | Missing, tampered, malformed, and expired tokens all return HTTP 400; a valid token succeeds | Confirmed | `tests/test_csrf.py` — all 7 tests PASSED (missing/tampered/malformed/expired/valid/GET-exempt/real-config-enabled) | Pass |
| V-12 | Selenium end-to-end registration | Headless Chrome completes the happy-path and mismatched-password scenarios using explicit waits | Confirmed, not skipped (Chrome 155.0.8059.40 available) | `pytest -v -m ui` → 2 passed in 11.13s (Section 5) | Pass |
| V-13 | Local page-load performance | Median of 5 measured GET `/register` requests (after 1 warm-up) is under 2.0s | Confirmed. Measured durations (s): `[0.00111, 0.00065, 0.00045, 0.00058, 0.00057]`; median = `0.00058s` | `pytest -q -m performance -s` output (Section 5) | Pass |
| V-14 | No secret, password or database committed | `git ls-files` contains no `.env`, `.db`, `.sqlite`, private key, or `.pem` file | Confirmed — no matches | `git ls-files \| Select-String ...` (Section 5); `tests/test_security_edge_cases.py::test_git_tracked_files_exclude_env_and_database_and_key_files` PASSED | Pass |
| V-15 | Coverage, Ruff and dependency audit | Coverage ≥85%, Ruff clean, pip-audit clean | Confirmed — 100% coverage, `ruff check .` clean, `pip-audit` clean | Sections 2–3 | Pass |

## 5. Selenium Result

```text
$ python -m pytest -v -m ui
tests/ui/test_registration_ui.py::test_register_valid_submission_shows_registration_successful PASSED [ 50%]
tests/ui/test_registration_ui.py::test_register_mismatched_passwords_shows_error_and_clears_password_fields PASSED [100%]

===================== 2 passed, 117 deselected in 11.13s ======================
```

Both Selenium tests passed using a locally installed headless Google Chrome 155.0.8059.40, auto-provisioned via Selenium Manager (no manual ChromeDriver install). Neither test was skipped. No `screenshots/` directory was created, confirming no UI test failure occurred (the fixture only writes a screenshot on failure).

Performance evidence:

```text
$ python -m pytest -q -m performance -s
Measured GET /register durations (s): [0.0011136999819427729, 0.0006532999686896801, 0.00044659996638074517, 0.0005808999994769692, 0.0005706999800167978]
Median GET /register duration (s): 0.0005808999994769692
1 passed in 0.75s
```

## 6. UI Evidence Index

No new screenshots were generated during this verification pass (Selenium tests passed; the fixture captures screenshots only on failure). Prior pipeline-stage evidence remains in `evidence/`:

```text
.gitkeep
step-00-project-tree.txt
step-00-tool-versions.txt
step-01-clarification-questions.png
step-03-architecture-diff.txt
step-pipeline-agent-inventory.txt
step-pipeline-githooks-tree.txt
step-pipeline-github-tree.txt
step-pipeline-gitlog.txt
step-pipeline-precommit-blocked.png
step-pipeline-status.png
```

No new screenshot evidence was required for Step 7 since no Selenium failure occurred.

## 7. Security Verification

| Check | Result | Evidence |
|---|---|---|
| Submitted password never in response | Pass | `tests/test_security_edge_cases.py` (4 tests covering success/validation-failure/duplicate/DB-failure) PASSED |
| Submitted password never logged | Pass | `tests/test_security_edge_cases.py::test_register_success_plain_password_never_logged`, `::test_register_database_failure_plain_password_never_logged` PASSED |
| Password hash never in response | Pass | `tests/test_security_edge_cases.py::test_register_success_response_never_contains_password_hash` PASSED |
| CSRF token never logged | Pass | `tests/test_security_edge_cases.py::test_register_valid_csrf_token_never_appears_in_logs` PASSED |
| Parameterized SQL only | Pass | `src/registration_app/repository.py` uses `?` placeholders exclusively; `tests/test_repository.py::test_create_user_uses_parameterized_sql_not_string_interpolation` PASSED |
| SQL-injection-shaped input handled as data | Pass | `tests/test_repository.py` (full_name/email), `tests/test_routes.py::test_register_post_sql_injection_shaped_input_handled_as_data` PASSED |
| Raw SQLite error never exposed | Pass | `tests/test_security_edge_cases.py::test_register_database_failure_response_contains_only_generic_message` PASSED |
| Rollback on DB failure | Pass | `src/registration_app/repository.py:80,86` call `connection.rollback()` in both exception branches |
| CSRF enforced (missing/tampered/malformed/expired rejected) | Pass | `tests/test_csrf.py` (Section 4, V-11) |
| No `.env`/key/database committed | Pass | Section 4 (V-14) |

## 8. Requirement-Verification Matrix

All functional requirements (FR-1–FR-16), non-functional requirements (NFR-1–NFR-8), security requirements (SEC-1–SEC-8), and design-review decisions (ADD-1, ADD-2, ADD-5) were traced to implementation and tests in `docs/05-code-review.md` Section 4 (Requirement-Verification Matrix), which this verification pass re-confirms unchanged: all rows remain `Pass` against the same commit (`7b8bed3e`).

## 9. Defects Found

None. No High, Medium, or Low defect was identified during this verification pass.

## 10. Known Limitations

- Performance (V-13) was measured using the Flask test client only (server-side, in-process), not full browser page-load time; this is explicitly documented in `tests/test_performance.py` per NFR-4's approved scope.
- Selenium (V-12) was verified only against a locally installed Chrome 155.0.8059.40 on Windows; the dedicated `browser-tests` CI job (`.github/workflows/ci.yml`, `ubuntu-latest`) has not yet had its first actual GitHub Actions run, since this repository's work has not been pushed. That first CI run remains deferred, per `docs/04-impl-plan.md` T12's done criteria, to after push.
- One uncommitted, unrelated documentation metadata edit exists in the working tree (`docs/01-requirements.md` `Status` field), disclosed in `docs/05-code-review.md` CR-1 (deferred, non-blocking).

## 11. Final Verdict

**Pass.** All 15 verification scenarios (V-1–V-15) pass with real, reproducible command evidence. 119/119 tests pass, coverage is 100% (exceeding the 85% target), `ruff check .` and `pip-audit` are both clean, no secret or database file is committed, Selenium passed without skip, and the measured performance median (≈0.00058s) is well under the 2.0s threshold.

---

**Gate:** Approve step 7 and continue? (yes / changes needed)
