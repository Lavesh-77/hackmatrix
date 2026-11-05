# Git Workflow

A deliberately small workflow: one stable branch, one feature branch per task, the Team Lead merges.

- `main` — stable, integrated, demo-ready.
- `feature/<task-id>-<short-name>` — one task or a small related group.

Branch protection and mandatory approvals are **not** assumed. This works by convention plus the Team Lead's review. Nobody but the Team Lead merges into `main`.

## 1. Initial clone (once per machine)

```bash
git clone <repository-url>
cd <repository-name>
```

```powershell
# Windows PowerShell
git clone <repository-url>
cd <repository-name>
```

Verify you are on `main` and up to date:

```bash
git switch main
git pull origin main
```

If `git switch` is not available (Git older than 2.23), use `git checkout main`.

## 2. Start a task

Always start from the latest `main`:

```bash
git switch main
git pull origin main
git switch -c feature/task-name
```

Example:

```bash
git switch -c feature/T-003-login-ui
```

One branch per task. Do not reuse a branch for unrelated work.

## 3. Work, commit, push

```bash
git status
git add .
git commit -m "T-003: add login form UI"
git push -u origin feature/T-003-login-ui
```

Rules:

- Review `git status` and the diff before committing. Do not commit `.env`, build output, or dependencies.
- Commit messages start with the task ID and describe the change.
- Commit as often as is useful locally; push at least once per work session.
- Before pushing, confirm the app still builds and the changed behaviour works.

## 4. Optional: open a pull request

Local review and merge is the default for this workflow. A pull request is optional bookkeeping; use it only if you want the GitHub diff view and comment history. Branch protection is not assumed.

GitHub shows **Compare & pull request** after a branch is pushed. Otherwise: **Pull requests → New pull request**, base `main`, compare your feature branch.

In the description, include:

```text
Task(s): T-003
What changed:
How to test:
Environment / integration notes:
```

The Team Lead reviews, comments, and merges. Delete the branch after merging.

If the team prefers to skip pull requests, the Team Lead can review and merge locally:

```bash
git fetch origin
git switch main
git pull origin main
git merge --no-ff feature/T-003-login-ui
git push origin main
```

Either way, the Team Lead is the only person who merges.

### Review branch (recommended)

Test the developer's work on a disposable copy, so any small fix does not land on their branch:

```bash
git fetch origin
git switch -c review/T-003 origin/feature/T-003
git merge origin/main
# build, start, test
```

Then merge the review branch into `main` with `--no-ff`, push, delete it, and delete the feature branch. The review branch is local and temporary; it is never pushed.

## 5. After integration

Every developer syncs before starting the next task:

```bash
git switch main
git pull origin main
```

Then delete the merged local branch:

```bash
git branch -d feature/T-003-login-ui
```

And the remote branch, if it was not deleted on GitHub:

```bash
git push origin --delete feature/T-003-login-ui
```

## 6. Keeping a branch current

If `main` moved while you were working, bring it into your branch:

```bash
git switch feature/T-003-login-ui
git fetch origin
git merge origin/main
```

Resolve conflicts, commit the merge, push normally.

**Do not rebase a branch you have already pushed.** Rewriting shared history requires a force-push, which is forbidden.

If a conflict is in a file you do not own, stop and ask the Team Lead. Do not resolve someone else's code by guesswork.

## 7. Responsibilities

### Developers (Veer, Lavesh)

- Branch from an up-to-date `main` before starting.
- Work only on assigned tasks.
- Test before pushing.
- Push the branch and report to the Team Lead.
- Never push to `main`, never force-push, never merge.
- Sync `main` after every integration.

### Team Lead (Soorya)

- Keep `main` stable.
- Review every branch before merging: scope, contract compliance, secrets, build.
- Test on a temporary `review/<task-id>` branch, then merge it into `main` after approval.
- Merge and delete the branch.
- Resolve integration conflicts and update `docs/TASKS.md`.
- Handle the initial setup commit, the only allowed direct commit to `main`.
- Recover from mistakes without rewriting shared history (revert, do not force-push).

## 8. Windows and line endings

- `.gitattributes` normalizes line endings, so Windows and Linux diffs stay clean.
- Git for Windows normally configures `core.autocrlf=true`; keep that default.
- If a diff shows every line changed for no reason, check:

  ```powershell
  git config --get core.autocrlf
  ```

  Set it if missing:

  ```powershell
  git config --global core.autocrlf true
  ```

- Use forward slashes in committed paths and configuration files, even on Windows.
- Line continuation differs: use `\` in Bash and a backtick `` ` `` in PowerShell. Never copy multi-line shell snippets across shells without adjusting.

## 9. Forbidden commands

| Command | Why |
| --- | --- |
| `git push --force` / `--force-with-lease` | Rewrites shared history |
| `git reset --hard` on a shared branch | Discards other people's commits |
| `git clean -fd` | Deletes untracked work, including files an agent just created |
| `git commit` directly on `main` | Breaks the integration model |
| `git checkout <someone else's branch>` then committing | Mixes ownership |
| `git push origin main` (developers) | Only the Team Lead merges |

## 10. Common situations

**I edited files while on `main`.**
Create the branch before committing; the changes carry over:

```bash
git switch -c feature/T-003-login-ui
```

**I committed on `main` locally but have not pushed (Team Lead only).**
Move the commit to a branch first, then reset local `main` to the remote:

```bash
git switch -c feature/T-003-login-ui
git switch main
git reset --hard origin/main
```

This recovery step is for the Team Lead. The general "no `git reset --hard`" rule exists to protect uncommitted work and other people's commits.

**I already pushed to `main`.**
Tell the Team Lead immediately. Do not force-push. The Team Lead decides whether to revert the commit.

**My push was rejected.**
Your branch is behind the remote version of the same branch:

```bash
git pull --no-rebase origin feature/T-003-login-ui
git push
```

**I am in a detached HEAD.**
Create a branch from where you are, or return to `main`:

```bash
git switch -c feature/T-003-recovered
```

**I do not know what state I am in.**
Run `git status` and `git branch --show-current`, and send both outputs to the Team Lead.
