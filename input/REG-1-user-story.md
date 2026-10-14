# REG-1 — User Registration

| Field | Value |
|---|---|
| Issue key | REG-1 |
| Type | Story |
| Priority | High |
| Reporter | Product Owner |
| Assignee | Parag Bansal |
| Status | To Do |
| Source | Local ticket file replacing JIRA |

## User Story

**As a** new visitor,
**I want** to create an account using my name, email address and password,
**so that** I can access registered-user features in the future.

## Acceptance Criteria

### AC1 — Display the registration page

Given I am a new visitor,
when I navigate to `/register`,
then I see:

- Full Name
- Email
- Password
- Confirm Password
- Register button

### AC2 — Successful registration

Given I enter valid information,
when I submit the registration form,
then:

- One account is created.
- The password is stored as a secure hash rather than plain text.
- I see `Registration successful`.
- Neither the password nor its hash is displayed.

### AC3 — Required fields

Given one or more fields are empty,
when I submit the form,
then:

- No account is created.
- A validation message is shown for each missing field.
- Non-password fields remain populated.
- Password fields are cleared.

### AC4 — Email validation

Given I enter an invalid email address,
when I submit the form,
then:

- No account is created.
- I see `Enter a valid email address`.

### AC5 — Password confirmation

Given Password and Confirm Password are different,
when I submit the form,
then:

- No account is created.
- I see `Passwords do not match`.

### AC6 — Password rules

A valid password contains:

- At least eight characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

If the password does not meet these rules, no account is created and a clear validation
message is displayed.

### AC7 — Duplicate email

Given an account already exists for an email address,
when I submit the same email using the same or different letter casing,
then:

- A second account is not created.
- I see `An account with this email already exists`.

Email comparison is case-insensitive.

### AC8 — Safe database error handling

If registration cannot be completed due to an unexpected database error:

- No partial account is created.
- The transaction is rolled back.
- Passwords, hashes, SQL statements and database details are not displayed.
- The user sees `Registration could not be completed. Please try again`.

## Non-Functional Expectations

- Python 3.11 or later.
- Passwords are never stored or logged in plain text.
- Submitted HTML or script must not execute.
- The registration page should load in under two seconds locally.
- At least 85% line coverage.
- Tests must not use an external database or external API.

## Open Questions

- What are the maximum lengths for each field?
- How should leading and trailing whitespace be handled?
- What happens immediately after successful registration?
- Which CSRF implementation should be used?
- Which browsers must be supported?
- Should the full name allow numbers or punctuation?
- How should database transactions and connection lifetimes be managed?

## Out of Scope

- Login and logout
- Email verification
- Password reset
- CAPTCHA
- Social login
- User profile
- Administration
- Production deployment