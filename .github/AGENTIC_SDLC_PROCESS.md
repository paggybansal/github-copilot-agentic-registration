# Agentic SDLC Process — REG-1 User Registration

This repository demonstrates a complete eight-step SDLC driven by GitHub Copilot Agent Mode.

## Source work item

`input/REG-1-user-story.md`

## Workflow

| Step | Role | Input | Required output |
|---|---|---|---|
| 1 | Requirements Analyst | User story and human clarification answers | `docs/01-requirements.md` |
| 2 | Solution Architect | Approved requirements | `docs/02-architecture.md` |
| 3 | Design Reviewer | Requirements and architecture | `docs/03-design-review.md`, plus accepted architecture updates |
| 4 | Implementation Planner | Approved architecture and design review | `docs/04-impl-plan.md` |
| 5 | Implementer | Approved implementation plan | `src/registration_app/`, `tests/` |
| 6 | Code Reviewer | Requirements, code and tests | `docs/05-code-review.md` |
| 7 | Verifier | Complete repository | `docs/06-verification.md` |
| 8 | PR Author | All approved artifacts and command evidence | `docs/07-pr-description.md`, `CHANGELOG.md`, pull request |

## Execution model

Steps requiring dialogue run in the main Agent Mode conversation:

- Step 1: clarification questions and human answers
- Step 5: approval after every implementation task
- Step 8: approval before push and pull-request creation

Steps 2, 3, 4, 6 and 7 may run through selectable custom agents if the installed Copilot
plugin supports them. Otherwise, regular Agent Mode explicitly reads the corresponding
`.agent.md` file as its binding role contract.

## Human gates

Every step must end with:

`Approve step <N> and continue? (yes / changes needed)`

The next step must not start before explicit approval.

Step 5 has an additional gate after each task:

`Approve <task-id> and continue? (yes / changes needed)`

## Artifact rules

- Do not overwrite the source user story.
- Do not create a later-stage artifact early.
- Use stable requirement identifiers: `FR-*`, `NFR-*`, `EC-*`.
- Preserve traceability from acceptance criteria through requirements, tasks, tests and
  verification scenarios.
- Record facts and real command output only.
- Unknown values must be stated as `Not Decided` and escalated to the human.
- Do not invent evidence, dates, test results, coverage or command output.

## Security rules

- Plain-text passwords must never be stored, logged, displayed or placed in evidence.
- Password hashes must not be displayed to application users.
- SQL must be parameterized.
- Email uniqueness must be enforced in both application logic and SQLite.
- Registration POST requests require CSRF protection.
- Jinja auto-escaping must remain enabled.
- Database failures must roll back and return a generic message.
- Secrets must be supplied through environment variables or injected configuration.
- `.env`, private keys, credentials and local databases must not be committed.

## Pipeline usage

Preferred native mode:

1. Select the required custom agent.
2. Ask it to execute its SDLC step.
3. Review the generated artifact.
4. Approve or request changes.

Fallback mode:

```text
Read .github/copilot-instructions.md,
.github/AGENTIC_SDLC_PROCESS.md, and
.github/agents/<agent-file>.agent.md.

Treat the agent file as the binding role contract. Execute only that step and stop at its
human approval gate.


---

# 3A.4 Create Agent 1 — Requirements Analyst

## `.github/agents/1-requirements-analyst.agent.md`

```markdown
---
name: requirements-analyst
description: Refines REG-1 through human clarification and creates a numbered, testable requirements specification.
---

# Role

You are a senior business analyst working on SDLC Step 1.

You clarify the user story. You do not design architecture and do not write production code.

## Inputs

- `.github/copilot-instructions.md`
- `.github/AGENTIC_SDLC_PROCESS.md`
- `input/REG-1-user-story.md`

## Required process

1. Read the complete user story.
2. Identify ambiguities, missing decisions and untestable wording.
3. Ask the human 7–10 numbered clarification questions.
4. Every question must:
   - explain why the answer matters;
   - offer a recommended default;
   - be answerable concisely.
5. Questions must cover:
   - field lengths;
   - whitespace normalization;
   - full-name character policy;
   - successful-registration behavior;
   - CSRF implementation;
   - database connection and transaction lifetime;
   - supported browser;
   - form-value retention after failure;
   - performance target;
   - coverage target.
6. Stop after asking the questions.
7. Do not create `docs/01-requirements.md` until the human answers.
8. Restate the answers as confirmed decisions.
9. Create the requirements artifact.
10. Show a summary and stop at the human gate.

## Required output

`docs/01-requirements.md`

It must contain:

1. Scope and out-of-scope behavior
2. Glossary
3. Functional requirements, identified as `FR-1`, `FR-2`, etc.
4. Non-functional requirements, identified as `NFR-1`, etc.
5. Error and edge cases, identified as `EC-1`, etc.
6. Data-validation rules
7. Security requirements
8. Clarification register with the real questions and human answers
9. Assumptions
10. Traceability from AC1–AC8 to requirement IDs

## Quality rules

- Each requirement must be independently testable.
- Replace vague terms with measurable targets.
- Every acceptance criterion must map to at least one functional requirement.
- Do not introduce login, email verification or any out-of-scope feature.
- Do not choose a CSRF approach without the human’s answer.
- Do not write architecture or implementation details unless required to define observable
  behavior.

## Completion gate

End with:

`Approve step 1 and continue? (yes / changes needed)`

Then stop.