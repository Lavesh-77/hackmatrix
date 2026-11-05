---
description: Review pushed branches, test them, and merge approved work into main
---

You are running the integration loop as the Team Lead's agent.

Target: $ARGUMENTS

If the target is empty, review all branches that are not yet merged into `main`, one at a time. If the target names a task ID or branch, start with that one.

Before anything else:

1. Read `AGENTS.md`, then `roles/team-lead.md`.
2. Read `docs/API_CONTRACT.md`, `docs/TASKS.md`, `workflows/git-workflow.md`, and `workflows/integration-checklist.md`.
3. Run `git status`. If the working tree has uncommitted changes, stop and ask the Team Lead what to do with them.

## 1. Find the work

```bash
git fetch origin --prune
git branch -r --no-merged main
```

Ignore `origin/main` itself. For each remaining branch, show:

- the branch name and the task ID it refers to;
- the owner according to `docs/TASKS.md`;
- `git diff --stat main...origin/<branch>`;
- whether it touches `docs/`, `.env`, lockfiles, or files owned by someone else.

If more than one branch is ready, propose a merge order: foundational or lowest-risk first, and anything another branch depends on before its dependants. Ask the Team Lead to confirm the order unless they already named a target.

## 2. Review one branch

Create a disposable review branch:

```bash
git switch -c review/<task-id> origin/<branch>
git merge origin/main
```

Resolving conflicts:

- If the conflict is in generated files, formatting, imports, or clearly separate sections, resolve it.
- If both sides changed the same business logic and the file is owned by Veer or Lavesh, stop and show the Team Lead both versions before choosing.
- Never force-push. Never rewrite the feature branch's history.

Then check the change against the contract:

- paths, methods, field names, types, status codes, error shape;
- no invented endpoints, fields, or tables;
- no secrets, `.env` files, or credentials;
- no unnecessary dependencies;
- no edits to `docs/`, `AGENTS.md`, or role documents;
- no unrelated refactors.

## 3. Test it

Install dependencies, build, start the app, and exercise the changed flow, including at least one error or empty state.

Apply `workflows/integration-checklist.md`. Report the result as a short list:

```text
Branch: feature/T-003-login-ui
Task(s): T-003
Owner: Veer
Contract: matches / mismatch: <detail>
Build: pass / fail
Flow tested: <what you ran and saw>
Checklist: pass / fail: <item>
Risks: <anything the Team Lead should know>
```

If anything fails, do not merge. Report exactly what failed and what "fixed" looks like. Wait for instructions.

## 4. Wait for approval

Do not merge until the Team Lead explicitly approves.

A small fix that is clearly within the task scope may be committed on the review branch, but say so in the report. Anything larger goes back to the owner.

## 5. Merge

After approval:

```bash
git switch main
git pull origin main
git merge --no-ff review/<task-id>
git push origin main
```

Then:

1. Run the build and the changed flow once on `main`.
2. Delete the review branch: `git branch -d review/<task-id>`.
3. Delete the feature branch locally and remotely only after the push succeeded:

   ```bash
   git branch -d feature/<task-id>-<name>
   git push origin --delete feature/<task-id>-<name>
   ```

4. Update `docs/TASKS.md`: set completed tasks to `Completed`, keep partial work at `In Progress`, and add any follow-up tasks the review exposed.
5. Draft the sync message for the Team Lead:

```text
Merged <task IDs> into main.
Both of you: git switch main && git pull origin main before your next task.
```

## 6. Repeat

For every remaining branch:

- merge the updated `origin/main` into its review branch **before** testing;
- test the combined result, not the branch in isolation;
- ask for approval again.

Finish with a summary: branches merged, branches rejected and why, tasks updated, and what the Team Lead should tell the developers.

Never push to `main` without the Team Lead's approval. Never force-push. Never merge a branch whose build or tests fail.
