---
description: Orchestrate the complete REG-1 SDLC while stopping at every human approval gate.
mode: agent
---

# REG-1 Agentic SDLC Orchestrator

Act as the REG-1 Agentic SDLC orchestrator.

## Read first

Read:

- `.github/copilot-instructions.md`
- `.github/AGENTIC_SDLC_PROCESS.md`
- all files under `.github/agents/`
- all files under `.github/skills/`
- `input/REG-1-user-story.md`

## Initial status

First perform the same checks defined in:

` .github/prompts/sdlc-status.prompt.md`

Do not modify files during the status check.

Report:

```text
Step | Role | Artifact | Status