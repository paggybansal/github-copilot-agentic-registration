---
description: Report the current REG-1 Agentic SDLC status without modifying files.
mode: agent
---

# REG-1 SDLC Status

Read:

- `.github/copilot-instructions.md`
- `.github/AGENTIC_SDLC_PROCESS.md`

Do not create, edit, delete, stage, commit, or push any file.

## Artifact checks

Check the following:

| Step | Role | Completion evidence |
|---|---|---|
| 1 | Requirements Analyst | `docs/01-requirements.md` exists |
| 2 | Solution Architect | `docs/02-architecture.md` exists |
| 3 | Design Reviewer | `docs/03-design-review.md` exists |
| 4 | Implementation Planner | `docs/04-impl-plan.md` exists |
| 5 | Implementer | At least one production file exists under `src/registration_app/` other than `__init__.py` |
| 6 | Code Reviewer | `docs/05-code-review.md` exists |
| 7 | Verifier | `docs/06-verification.md` exists |
| 8 | PR Author | `docs/07-pr-description.md` exists |

## Repository checks

Run or inspect:

```text
git branch --show-current
git status --short
git log --oneline -10