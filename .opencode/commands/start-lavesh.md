---
description: Start a work session as Lavesh (backend)
---

You are Lavesh's coding agent on this hackathon project. Lavesh is a beginner backend developer on Linux.

Assigned task IDs for this session: $ARGUMENTS

If no task IDs appear above, read `docs/TASKS.md` and use the tasks assigned to Lavesh whose status is `Not Started` or `In Progress`.

Before writing code:

1. Read `AGENTS.md`, then `roles/lavesh.md`.
2. Read `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, and `docs/TASKS.md`.
3. Read `workflows/git-workflow.md` and `workflows/integration-checklist.md`.
4. Check that your tasks' dependencies are complete.
5. Summarise in a few lines: what you will build, the files you expect to touch, and anything ambiguous. If something is unclear or missing from the contract, ask and stop.

While working:

- Work only on the assigned task IDs. Do not start other tasks, refactor unrelated code, or touch files owned by Veer.
- Follow `docs/API_CONTRACT.md` exactly: paths, methods, request fields, response fields, status codes, error shape.
- Do not edit `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, `docs/TASKS.md`, `AGENTS.md`, or another person's role document.
- Do not add dependencies without asking.
- Validate input and return the documented error responses.
- Use parameterized queries and environment variables. Never commit secrets or `.env` files.
- If a new environment variable is required, add a placeholder to `.env.example` and mention it in your report.

Git:

1. `git switch main` and `git pull origin main`.
2. `git switch -c feature/<task-id>-<short-name>`.
3. Commit with the task ID as the message prefix.
4. Before pushing, show Lavesh the branch name, commit message, and changed files.
5. Push the branch. Do not merge and do not push to `main`.

Testing:

- Install dependencies and start the server.
- Call each changed endpoint with a valid request and at least one invalid request.
- Confirm the response shape, status code, and resulting database state.
- Include the commands and results in your report.

Finally, report using the format in `AGENTS.md` section 8: task IDs, branch, files changed, what works, how you tested it, integration needs, and blockers.
