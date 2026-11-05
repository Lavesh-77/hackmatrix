---
description: Start a work session as Veer (frontend)
---

You are Veer's coding agent on this hackathon project. Veer is a beginner frontend developer on Windows.

Assigned task IDs for this session: $ARGUMENTS

If no task IDs appear above, read `docs/TASKS.md` and use the tasks assigned to Veer whose status is `Not Started` or `In Progress`.

Before writing code:

1. Read `AGENTS.md`, then `roles/veer.md`.
2. Read `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, and `docs/TASKS.md`.
3. Read `workflows/git-workflow.md` and `workflows/integration-checklist.md`.
4. Check that your tasks' dependencies are complete.
5. Summarise in a few lines: what you will build, the files you expect to touch, and anything ambiguous. If something is unclear or missing from the contract, ask and stop.

While working:

- Work only on the assigned task IDs. Do not start other tasks, refactor unrelated code, or touch files owned by Lavesh.
- Follow `docs/API_CONTRACT.md` exactly. Do not invent endpoints, fields, or response shapes.
- Do not edit `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, `docs/TASKS.md`, `AGENTS.md`, or another person's role document.
- Do not add dependencies without asking.
- Handle loading, error, and empty states for data-driven views.
- Keep API base URLs in environment configuration, never hardcoded.
- Never commit secrets or `.env` files.

Git:

1. `git switch main` and `git pull origin main`.
2. `git switch -c feature/<task-id>-<short-name>`.
3. Commit with the task ID as the message prefix.
4. Before pushing, show Veer the branch name, commit message, and changed files.
5. Push the branch. Do not merge and do not push to `main`.

Testing:

- Install dependencies, build, and start the app.
- Exercise the happy path plus a validation error and an empty state.
- Report exactly what you ran and what you observed.

Finally, report using the format in `AGENTS.md` section 8: task IDs, branch, files changed, what works, how you tested it, integration needs, and blockers.
