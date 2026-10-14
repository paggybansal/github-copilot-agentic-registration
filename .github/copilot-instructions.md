# GitHub Copilot Instructions — Registration Capstone

## Current repository state

This repository contains:

1. An Agentic SDLC pipeline under `.github/`
2. A Flask registration application under `src/registration_app/`
3. Tests under `tests/`
4. SDLC artifacts under `docs/`

The source work item is `input/REG-1-user-story.md`.

## Mandatory behavior

- Do not skip SDLC stages.
- Do not implement production code before requirements, architecture, design review and
  implementation plan are approved.
- Never start the next stage without explicit human approval.
- Never invent requirements, command output, test results, dates or evidence.
- Ask the human when a business or security decision is missing.
- Make the smallest change necessary for the current approved task.
- Never expose secrets, passwords, password hashes, CSRF tokens or database details.
- Never create or edit `.env`, private-key files or local database files.
- Use `.env.example` only with empty placeholder values.
- Do not use real personal data in tests or screenshots.

## Technology constraints

- Python 3.11 or later.
- Flask application-factory pattern.
- SQLite through Python's built-in `sqlite3`.
- pytest for unit and integration tests.
- Selenium with pytest for UI automation.
- Ruff for linting.
- No ORM or frontend framework without human approval.
- No new runtime dependency without human approval.

## Security baseline

- Hash passwords with Werkzeug security functions.
- Never implement password hashing manually.
- Normalize email by trimming and lowercasing.
- Enforce email uniqueness in the application and database schema.
- Use parameterized SQL only.
- Keep Jinja auto-escaping enabled.
- Require CSRF protection for real state-changing form submissions.
- Password fields must never be repopulated.
- Roll back database transactions after failed writes.
- Return a generic user-facing message for internal database failures.
- Do not show tracebacks, SQL, filesystem paths, submitted passwords or password hashes.

## Testing baseline

- Every production task includes tests.
- Tests use temporary SQLite databases under pytest `tmp_path`.
- Tests make no external API calls.
- Selenium tests use `@pytest.mark.ui`.
- Performance tests use `@pytest.mark.performance`.
- From implementation onward, both must pass:

  `python -m pytest -q`

  `ruff check .`

- Target at least 85% line coverage until requirements define the final target.

## Human approval gates

End every SDLC stage with:

`Approve step <N> and continue? (yes / changes needed)`

Stop and wait after asking.

During implementation, complete one plan task at a time and ask:

`Approve <task-id> and continue? (yes / changes needed)`

## Git safety

- Never force-push.
- Never use `git reset --hard`.
- Never rewrite committed history without explicit permission.
- Never merge a pull request without explicit human approval.