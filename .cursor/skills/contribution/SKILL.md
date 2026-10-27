---
name: contribution
description: >-
  Plans a code change from an assigned GitHub issue. Use when the user
  invokes /contribution, starts work from an assigned issue, or asks
  what to do with an issue assigned to them.
disable-model-invocation: true
---

# Contribution

The person decides. Return a plan, then wait. Edit files only after they accept the plan in this conversation.

## Read

1. List issues assigned to the authenticated user on this repository. If they named one, use that issue.
2. Read the issue with `gh issue view`, including comments.
3. Read `AGENTS.md` at the repo root, the sections "Working on Issues" and "PR Body Style".
4. Read `docs/contribute/dev-contribute.mdx`, the sections "Issue first, code second" and "Using AI tools responsibly".
5. From the issue, identify the areas it touches. Read the nearest `AGENTS.md` for each area, including its Key Contracts. For a CLI change, that includes `src/prefect/cli/AGENTS.md`. For a test change, that includes `tests/AGENTS.md`.

## Plan

Return a short markdown plan with these parts:

- Issue number, title, and the behavior the issue asks for
- Acceptance criterion, in the issue's words
- Files the issue allows, and any file the issue leaves untouched
- Contracts that apply, each with its path
- Approach
- The targeted test command

Ask one question if the issue and the contracts disagree. Otherwise show the plan in the conversation and stop.

## After acceptance

- Write the test the issue requires so it fails for the reason the issue describes, then make the change.
- Stay inside the files the accepted plan names.
- Run the targeted test. Show the failing result and the passing result.
- Leave the pull request, the review, and the approval to the person.
