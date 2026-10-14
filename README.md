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

## Status

Repository scaffold only. Production implementation starts after SDLC Steps 1–4 are
approved.