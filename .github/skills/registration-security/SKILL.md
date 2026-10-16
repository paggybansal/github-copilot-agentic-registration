---
name: registration-security
description: Security standards for registration forms, password handling, SQLite persistence, email uniqueness, CSRF, XSS, and safe error responses.
---

# Registration Security Skill

Use this skill whenever designing, implementing, reviewing, or verifying REG-1.

## Password handling

- Accept passwords only through the registration form.
- Never log a submitted password.
- Never include a submitted password in exception text.
- Never display a submitted password after success or failure.
- Never repopulate Password or Confirm Password fields.
- Hash passwords using Werkzeug `generate_password_hash`.
- Verify password hashes only with Werkzeug `check_password_hash`.
- Never implement password hashing or cryptography manually.
- Store only the generated password hash in SQLite.
- Never show the complete password hash in screenshots, logs, responses, or mentor evidence.

Example:

```python
from werkzeug.security import check_password_hash, generate_password_hash

password_hash = generate_password_hash(password)
assert check_password_hash(password_hash, password)
```

## Email normalization

Before duplicate lookup or persistence:

1. Remove leading and trailing whitespace.
2. Convert the email to lowercase.
3. Validate the normalized value.
4. Use that same normalized value for both duplicate lookup and insertion.

Example:

```python
normalized_email = email.strip().lower()
```

Do not perform duplicate lookup using one value and insertion using another.

## Duplicate-email protection

Protect uniqueness at two levels.

### Layer 1 — application lookup

Check whether the normalized email already exists before insertion.

Purpose:

- Gives the user a friendly duplicate-email message.
- Avoids using a database exception for the normal duplicate flow.

### Layer 2 — SQLite unique constraint

The database schema must enforce uniqueness:

```sql
email TEXT NOT NULL UNIQUE
```

Purpose:

- Prevents two concurrent requests from creating the same account.
- Protects data integrity even if both requests pass the initial application lookup.

If SQLite raises an integrity error caused by duplicate email, convert it to:

```text
An account with this email already exists
```

Do not show a raw SQLite exception.

## SQL safety

Use parameterized SQL:

```python
connection.execute(
    "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
    (full_name, email, password_hash),
)
```

Never use:

```python
connection.execute(
    f"INSERT INTO users (full_name, email) VALUES ('{full_name}', '{email}')"
)
```

Never use:

- f-strings to insert user input into SQL;
- `%` formatting to insert user input into SQL;
- `.format()` to insert user input into SQL;
- string concatenation to construct SQL with user input.

## Transaction safety

- Open a connection for the smallest practical scope.
- Commit only after a successful insert.
- Roll back after a failed write.
- Always close the connection.
- Never leave a partially created account.
- Tests must use a temporary SQLite database under `tmp_path`.
- Production and tests must never write to a database committed to Git.

## CSRF protection

Every real registration POST request requires a valid CSRF token.

Tests may disable CSRF only through explicit test configuration.

Verification must cover:

- a valid CSRF token is accepted;
- a missing CSRF token is rejected;
- an invalid CSRF token is rejected.

Never:

- log a CSRF token;
- put a CSRF token in evidence;
- expose a CSRF token in an error;
- disable CSRF in production configuration.

## XSS and HTML safety

- Keep Jinja auto-escaping enabled.
- Do not apply `|safe` to user-provided values.
- Do not use `Markup` on submitted values.
- Do not construct HTML using string concatenation with submitted data.
- Keep business and validation logic out of HTML templates.
- Test a full name containing a script-shaped value.

Example input:

```html
<script>alert("registration-xss-test")</script>
```

Expected behavior:

- The script does not execute.
- If the value is displayed, it is escaped as text.
- The response must not contain executable user-provided markup.

## Input validation

Validation must occur on the server even if HTML attributes such as `required` are present.

The server must enforce:

- required fields;
- approved maximum lengths;
- valid email format;
- approved full-name rules;
- approved password-strength rules;
- password confirmation.

Client-side validation improves usability but is not a security boundary.

## Form-value retention

After validation failure:

- Full Name may remain populated.
- Email may remain populated.
- Password must be empty.
- Confirm Password must be empty.

Do not include submitted passwords in hidden fields or HTML attributes.

## Safe database-error handling

The approved user-facing message is:

```text
Registration could not be completed. Please try again
```

The user-facing response must not contain:

- submitted password;
- password hash;
- SQL;
- database path;
- table name;
- column name;
- stack trace;
- Flask secret;
- CSRF token;
- raw SQLite exception.

Internal logging must also exclude submitted password and CSRF values.

## Secret configuration

Secrets must come from environment variables or injected application configuration.

Never commit:

- `.env`;
- Flask secret values;
- private keys;
- credentials;
- SQLite database files.

`.env.example` may contain only empty placeholders.

## Required security tests

The test suite must include evidence that:

1. The stored password differs from the submitted password.
2. Werkzeug can verify the stored hash.
3. The plain password is absent from the HTTP response.
4. The plain password is absent from captured logs.
5. A duplicate email with different casing is rejected.
6. An SQL-injection-shaped input is handled as data.
7. An XSS-shaped full name cannot execute.
8. A missing CSRF token is rejected.
9. An invalid CSRF token is rejected.
10. A database failure rolls back and returns the generic message.
11. No `.env`, private key, credential, or SQLite database is tracked by Git.

## Security review questions

During design review, code review, and verification, explicitly ask:

- Can the submitted password reach logs or exception messages?
- Can a password or hash be displayed in HTML?
- Can duplicate accounts be created by concurrent requests?
- Is every SQL value passed through a parameter?
- Is CSRF enabled in real application configuration?
- Is user-provided markup escaped?
- Can a database failure expose internal details?
- Is a local database or secret staged or committed?