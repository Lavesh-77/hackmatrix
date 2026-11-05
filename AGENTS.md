# AGENTS.md

Shared rules for every OpenCode agent working in this repository. Read this file at the start of every session, before touching anything else.

## 1. Session start

1. Read this file.
2. Read your role document in `roles/`:
   - Team Lead → `roles/team-lead.md`
   - Veer → `roles/veer.md`
   - Lavesh → `roles/lavesh.md`

   The project commands `/start-lead`, `/start-veer`, and `/start-lavesh` do all of this for you. Use the one for your machine at the start of every session.
3. Read, in this order:
   - `docs/PROJECT_SPEC.md`
   - `docs/ARCHITECTURE.md`
   - `docs/API_CONTRACT.md`
   - `docs/TASKS.md`
4. Find your assigned task IDs and check their dependencies before starting.
5. Read `workflows/git-workflow.md` before your first commit of the session.

If a document is empty or missing information you need, ask the Team Lead. Do not invent requirements, endpoints, or architecture.

You are one of several independent agents on separate machines. You cannot see another agent's conversation, memory, or local files. Anything that is not committed to this repository does not exist for the rest of the team.

## 2. General rules

- Work only within your assigned scope and task IDs.
- Understand the task before editing files. If it is ambiguous, ask instead of guessing.
- Follow the agreed architecture and technology stack. Do not introduce a different framework, language, or library.
- Do not make major architectural decisions independently. Propose them to the Team Lead first.
- Follow `docs/API_CONTRACT.md` exactly: paths, methods, field names, types, status codes, and error shapes.
- Keep changes small and reviewable. Do not refactor unrelated code.
- Do not overwrite, revert, or delete another developer's work.
- Do not add dependencies unless the task requires them. If you think one is needed, ask the Team Lead first.
- Never hardcode secrets, API keys, tokens, passwords, or credentials. Use environment variables.
- Test your changes before reporting completion. "It should work" is not a test.
- Report blockers immediately. Do not work around a blocked dependency by inventing your own interface.

## 3. Documentation rules

All project documentation lives in `docs/`.

| File | Contents |
| --- | --- |
| `docs/PROJECT_SPEC.md` | Problem statement, solution, target users, requirements, MVP features, constraints |
| `docs/ARCHITECTURE.md` | Technology stack, architecture, folder structure, technical decisions |
| `docs/API_CONTRACT.md` | Endpoints, request/response formats, database schema, shared interfaces |
| `docs/TASKS.md` | Task assignments, ownership, priorities, dependencies, progress |

- Do not silently change shared requirements or contracts.
- `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, and `docs/TASKS.md` are owned by the Team Lead. Developers propose changes; they do not edit these files.
- If the implementation needs a contract change, stop and message the Team Lead with: what changed, why, and what it affects.
- If you are assigned documentation work, keep it inside `docs/` or the file named in the task.

## 4. Git rules

- Never commit directly to `main`. The only exception is the Team Lead's initial project-setup commit before development starts.
- Work on a feature branch: `feature/<task-id>-<short-name>` (for example `feature/T-003-login-ui`).
- Pull the latest `main` before starting new work.
- Write meaningful commit messages: `<TASK-ID>: <short summary>` (for example `T-003: add login form UI`).
- Run `git status` and review what you are committing before every commit.
- Never force-push.
- Never run `git reset --hard`, `git clean -fd`, or delete branches you did not create.
- Never commit secrets or credential-containing environment files. `.env` is ignored; `.env.example` is the shared template.
- Push your branch and report it. Do not merge your own work into `main`.

## 5. Authority and conflict priority

The Team Lead has final authority over:

- Technology stack
- System architecture
- Shared interfaces and API contracts
- Task allocation
- Integration decisions
- Deployment

If instructions conflict, follow this order:

1. Explicit instructions from the Team Lead
2. `docs/PROJECT_SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `docs/API_CONTRACT.md`
5. `docs/TASKS.md`

If information is missing, ask rather than inventing requirements.

## 6. Task IDs and status

- Task IDs use the form `T-001`, `T-002`, … and never change once created.
- Use the task ID in branch names and commit messages.
- Valid statuses in `docs/TASKS.md`: `Not Started`, `In Progress`, `Blocked`, `In Review`, `Completed`.
- Only the Team Lead edits `docs/TASKS.md`. You report status changes; you do not write them yourself.

## 7. Definition of done

Before reporting a task complete:

- [ ] The assigned task is implemented and nothing outside its scope was changed.
- [ ] The API contract is respected (or a change was approved first).
- [ ] The project builds and starts without errors.
- [ ] The changed feature was exercised manually or with tests.
- [ ] Loading, error, and empty states are handled where the task touches the UI.
- [ ] No secrets, debug leftovers, or commented-out code were committed.
- [ ] `git status` is clean and the branch is pushed.

## 8. Reporting format

Report to the Team Lead in this exact shape:

```text
Task(s): T-003, T-004
Branch: feature/T-003-login-ui
Files changed: <list>
What works: <short summary>
How I tested it: <commands, URLs, manual steps>
Integration needed: <env vars, migrations, contract changes, deployment steps>
Blockers / uncertainties: <none, or describe>
```

## 9. Forbidden actions

- Do not regenerate or overwrite `AGENTS.md` (for example with `/init`). Propose changes to the Team Lead.
- Do not edit another person's role document.
- Do not edit `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, or `docs/TASKS.md`. Propose changes to the Team Lead.
- Do not commit to `main`, force-push, or rewrite shared history.
- Do not install system-wide tools or change machine configuration as part of a task.
- Do not run destructive commands (`rm -rf`, database resets, `git reset --hard`, `git clean -fd`).
- Do not commit `.env`, credentials, tokens, or local database files.
- Do not invent endpoints, fields, or database tables that are not in `docs/API_CONTRACT.md`.

## 10. Environment

- Agents run on different operating systems: Linux (Team Lead, Lavesh) and Windows (Veer).
- Do not assume a specific shell, path separator, package manager, or installed tool.
- Give commands for both Bash and PowerShell when they differ.
- Keep committed files portable: relative paths, no machine-specific absolute paths, no personally installed tooling required.
