# GitHub Copilot Agentic Registration

A small Flask user-registration feature delivered through an eight-step Agentic SDLC
pipeline using GitHub Copilot Agent Mode.

## Project layers

| Layer | Purpose | Location |
|---|---|---|
| Agentic SDLC pipeline | Instructions, agents, prompts, skills and quality controls | `.github/` |
| Registration product | Flask UI, validation, security and SQLite persistence | `src/registration_app/` |
| Automated tests | Unit, integration and Selenium UI tests | `tests/` |
| SDLC artifacts | Requirements through pull-request description | `docs/` |
| Demonstration evidence | Screenshots and command transcripts | `evidence/` |

## Work item

`REG-1 — User Registration`

The local story replacing JIRA is:

`input/REG-1-user-story.md`

## Planned SDLC artifacts

| Step | Artifact |
|---|---|
| 1. Requirements | `docs/01-requirements.md` |
| 2. Architecture | `docs/02-architecture.md` |
| 3. Design Review | `docs/03-design-review.md` |
| 4. Implementation Plan | `docs/04-impl-plan.md` |
| 5. Implementation | `src/registration_app/`, `tests/` |
| 6. Code Review | `docs/05-code-review.md` |
| 7. Verification | `docs/06-verification.md` |
| 8. Pull Request | `docs/07-pr-description.md` |

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
flask --app registration_app.app run
```

Then open `http://127.0.0.1:5000/register` in a browser.

## Running tests

Run the non-UI unit and integration suite (unit, repository, route, security and
performance tests, excluding Selenium):

```powershell
python -m pytest -q -m "not ui"
```

Run only the Selenium browser tests (requires a local headless-capable Google Chrome
installation; the suite skips with an explicit reason if Chrome is unavailable):

```powershell
python -m pytest -v -m ui
```

Run the performance test:

```powershell
python -m pytest -q -m performance
```

Check line coverage (target: at least 85% of `src/registration_app`):

```powershell
python -m pytest --cov=src/registration_app --cov-report=term-missing
```

Lint with Ruff:

```powershell
ruff check .
```

## Continuous integration

`.github/workflows/ci.yml` runs on every push to `main`/`feature/**` branches and on pull
requests targeting `main`:

- `quality` — a matrix across `ubuntu-latest`/`windows-latest` and Python 3.11/3.12 running
  `ruff check .` and `pytest -q -m "not ui"`.
- `browser-tests` — runs on `ubuntu-latest` with Python 3.11, installs headless Google Chrome
  via Selenium's bundled driver management, and runs `pytest -m ui`. Failure screenshots (if
  any) are uploaded as a build artifact; no password values are ever included in screenshots.
- `dependency-audit` — runs `pip-audit` against installed dependencies.

## Status

SDLC Steps 1–5 (Requirements through Implementation) are complete for REG-1 User
Registration. The Flask registration feature (`GET`/`POST /register`, `GET
/register/success`) is implemented with validation, Werkzeug password hashing, a SQLite
repository layer, CSRF protection, and full unit, integration, security, performance and
Selenium UI test coverage. SDLC Steps 6–8 (Code Review, Verification, Pull Request) are
pending.