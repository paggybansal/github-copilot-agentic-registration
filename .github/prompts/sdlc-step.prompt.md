---
description: Run exactly one REG-1 SDLC step and stop at its human approval gate.
mode: agent
---

# Execute One REG-1 SDLC Step

Run exactly one SDLC step.

The requested step number is:

`${input:step:Enter a step number from 1 to 8}`

## Step-to-agent mapping

| Step | Agent contract |
|---|---|
| 1 | `.github/agents/1-requirements-analyst.agent.md` |
| 2 | `.github/agents/2-solution-architect.agent.md` |
| 3 | `.github/agents/3-design-reviewer.agent.md` |
| 4 | `.github/agents/4-implementation-planner.agent.md` |
| 5 | `.github/agents/5-implementer.agent.md` |
| 6 | `.github/agents/6-code-reviewer.agent.md` |
| 7 | `.github/agents/7-verifier.agent.md` |
| 8 | `.github/agents/8-pr-author.agent.md` |

## Prerequisite artifacts

| Requested step | Required prerequisite |
|---|---|
| 1 | `input/REG-1-user-story.md` |
| 2 | `docs/01-requirements.md` |
| 3 | `docs/01-requirements.md` and `docs/02-architecture.md` |
| 4 | `docs/01-requirements.md`, `docs/02-architecture.md`, and `docs/03-design-review.md` |
| 5 | `docs/04-impl-plan.md` |
| 6 | Completed implementation and tests |
| 7 | `docs/05-code-review.md` with an approved final verdict |
| 8 | `docs/06-verification.md` with a Pass or Pass with limitations verdict |

## Procedure

1. Read:
   - `.github/copilot-instructions.md`;
   - `.github/AGENTIC_SDLC_PROCESS.md`;
   - the matching agent contract;
   - the relevant skill files under `.github/skills/`;
   - all prerequisite artifacts.

2. Treat the selected agent file as the binding role contract.

3. Verify the prerequisite artifacts before doing work.

4. If a prerequisite is missing or unapproved:
   - do not create the requested artifact;
   - report the missing prerequisite;
   - state which earlier step must run;
   - stop.

5. Execute only the requested step.

6. Do not begin work belonging to the following step.

7. Follow the agent's output contract exactly.

8. Before presenting the gate, report:
   - files created;
   - files modified;
   - requirements or findings addressed;
   - commands actually run;
   - actual command results;
   - unknown or undecided items;
   - deviations from the approved process;
   - completion checklist.

9. Ask the required human approval question.

10. Stop and wait for the human.

## Implementation-specific rule

For Step 5:

- Execute only one task from `docs/04-impl-plan.md` at a time.
- Add tests in the same task.
- Run the required quality commands.
- Ask:

  `Approve <task-id> and continue? (yes / changes needed)`

- Do not start the next task until approved.

## Prohibitions

Do not:

- fabricate command output;
- fabricate dates;
- fabricate test or coverage results;
- invent requirements;
- expose passwords, hashes, CSRF tokens, secrets, or database content;
- silently broaden the task;
- stage, commit, push, or merge unless the relevant contract and human approval permit it.