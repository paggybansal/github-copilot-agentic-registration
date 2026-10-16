---
name: python-test-standards
description: pytest, Flask test-client, SQLite, coverage, performance, and Selenium standards for the REG-1 registration application.
---

# Python and UI Test Standards

Use this skill whenever adding, reviewing, or verifying tests.

## Test structure

Use Arrange, Act, Assert.

Example:

```python
def test_duplicate_email_with_different_case_rejects_second_user(
    client,
    create_user,
):
    # Arrange
    create_user(email="new.user@example.test")

    # Act
    response = client.post(
        "/register",
        data={
            "full_name": "New User",
            "email": "NEW.USER@EXAMPLE.TEST",
            "password": "Example123",
            "confirm_password": "Example123",
        },
    )

    # Assert
    assert response.status_code == 200
    assert b"An account with this email already exists" in response.data
```

## Naming standards

Test files:

```text
tests/test_<module>.py
tests/ui/test_<feature>_ui.py
```

Test functions:

```text
test_<unit>_<condition>_<expected_result>
```

Examples:

```text
test_normalize_email_mixed_case_returns_lowercase
test_validate_email_missing_at_returns_error
test_validate_password_missing_uppercase_returns_error
test_register_duplicate_email_different_case_rejects_second_user
test_register_database_error_returns_generic_message
```

## Test isolation

- Use `tmp_path` for every SQLite database.
- Never use the local database under `instance/`.
- Never depend on test execution order.
- Never share mutable database state between tests.
- Never use real personal information.
- Use fictional domains such as `example.test`.
- Do not make external API calls.
- Clean up browser and server processes in fixtures.
- Tests must pass independently and in any order.

## Test data

Use obvious fictional data:

```text
Full name: New User
Email: new.user@example.test
Password: Example123
```

Do not include the test password in screenshots or committed evidence.

When a test must inspect password persistence:

- Assert that stored value differs from the submitted password.
- Verify it with Werkzeug.
- Do not print the complete stored hash.

## Required validation unit tests

Include tests for:

- email normalization;
- valid email;
- missing `@`;
- missing domain;
- leading/trailing email whitespace;
- missing full name;
- full-name maximum length;
- approved full-name character policy;
- password minimum length;
- password missing uppercase;
- password missing lowercase;
- password missing number;
- password confirmation mismatch;
- valid password;
- password hashing;
- password-hash verification.

## Required repository/database tests

Include tests for:

- user insertion;
- lookup by normalized email;
- duplicate normalized email;
- SQLite unique constraint;
- successful transaction commit;
- failed transaction rollback;
- connection cleanup;
- parameterized SQL behavior;
- SQL-injection-shaped input stored or handled as data.

## Required Flask integration tests

Include:

- GET `/register`;
- successful registration;
- every required field;
- invalid email;
- weak-password variants;
- password mismatch;
- duplicate email;
- duplicate email using different casing;
- non-password field retention after validation failure;
- password fields not retained;
- XSS-shaped full name escaped;
- SQL-injection-shaped input handled safely;
- database failure rollback;
- generic database-error response;
- plain password absent from response;
- plain password absent from logs;
- missing CSRF token rejected;
- invalid CSRF token rejected;
- valid CSRF token accepted.

## Flask test configuration

The application must allow test configuration to inject:

- a temporary database path;
- a deterministic test secret;
- explicit CSRF behavior;
- `TESTING=True`.

Do not read or write `.env` during tests.

## Selenium test rules

Mark browser tests:

```python
@pytest.mark.ui
```

Selenium tests must:

- use explicit waits;
- avoid `time.sleep`;
- locate elements using stable IDs, names, labels, or accessible roles;
- close the browser through fixture cleanup;
- use unique fictional emails;
- verify visible user behavior;
- avoid exposing submitted passwords in screenshots;
- save screenshots only for failures or planned evidence checkpoints.

Minimum end-to-end scenario:

```text
Open /register
→ verify the form fields
→ enter valid fictional data
→ submit
→ verify "Registration successful"
```

Recommended additional UI scenario:

```text
Open /register
→ enter mismatched passwords
→ submit
→ verify "Passwords do not match"
→ verify password fields are empty
```

## Explicit waits

Use Selenium explicit waits:

```python
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

message = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located(("id", "success-message"))
)
```

Do not use fixed sleeps such as:

```python
time.sleep(5)
```

## UI test environment

The Selenium fixture must:

1. Start the Flask application using a temporary database.
2. Wait until the server is ready.
3. Start the browser.
4. Yield control to the test.
5. Quit the browser.
6. Stop the Flask server.
7. Remove temporary resources.

If Chrome or a compatible driver is unavailable, the test may be skipped only with an explicit reason.

## Performance tests

Mark wall-clock-sensitive tests:

```python
@pytest.mark.performance
```

Performance tests must:

- use the target defined in approved requirements;
- describe the fixture and machine limitations;
- avoid external network calls;
- report the measured duration;
- use a reasonable hard threshold that avoids normal CI jitter.

## Coverage

Run:

```text
python -m pytest --cov=src/registration_app --cov-report=term-missing
```

The final target comes from approved requirements.

Until then, use at least:

```text
85% line coverage
```

Do not exclude difficult code merely to increase the percentage.

Any uncovered production line must be listed in the verification document.

## Non-UI quality gate

During normal implementation tasks, run:

```text
python -m pytest -q -m "not ui"
ruff check .
```

Selenium should run:

- at its implementation task gate;
- during Step 7 verification;
- in the dedicated CI browser job when configured.

## Assertion standards

- Assert observable behavior.
- Do not assert only implementation details.
- One test should have one primary behavioral purpose.
- Do not weaken assertions merely to make production code pass.
- Do not mock the function or component being tested.
- Use specific exceptions with `pytest.raises`.
- A skipped test must have a specific reason.
- A Selenium failure must be reported and must not be silently converted to a pass.

## Evidence standards

Test evidence may include:

- pytest summary;
- coverage table;
- Selenium result;
- browser screenshot without password values;
- response status and safe message;
- confirmation that the stored password value is a hash.

Test evidence must not include:

- submitted password;
- full password hash;
- CSRF token;
- Flask secret;
- local database content containing sensitive values;
- real user information.