# Integration Checklist

Run these checks at each hand-off. They exist because three independent agents will produce three locally-correct pieces that do not necessarily fit together.

Copy a section into the pull request description or your notes if that helps. Tick only what you actually verified.

## 1. Before assigning tasks

- [ ] `docs/PROJECT_SPEC.md` exists and defines the MVP.
- [ ] `docs/ARCHITECTURE.md` names the stack, folder structure, and environment variables.
- [ ] `docs/API_CONTRACT.md` covers every endpoint the frontend needs, with request and response shapes.
- [ ] Database schema in the contract matches the endpoints.
- [ ] Shared data types are named and defined once.
- [ ] Error response shape and status codes are agreed.
- [ ] `docs/TASKS.md` has IDs, owners, priorities, dependencies, and completion criteria.
- [ ] Each developer has at least one unblocked `High` priority task.
- [ ] File and folder ownership is unambiguous (who edits what).
- [ ] Required accounts, API keys, and hosting access exist — and none are committed.
- [ ] `.env.example` lists every variable, with placeholder values only.
- [ ] Setup committed and pushed; all machines can clone it.
- [ ] Role documents match this project's actual split.

## 2. Before implementation begins (per developer)

- [ ] Repository cloned; `git status` is clean.
- [ ] `AGENTS.md` and the assigned role document have been read by the agent this session.
- [ ] Kickoff command works (`/start-veer` or `/start-lavesh`).
- [ ] Model/provider is configured on that machine.
- [ ] Required runtimes and tools are installed (versions match the architecture).
- [ ] Project dependencies install without errors.
- [ ] App builds and starts locally.
- [ ] Local `.env` created from `.env.example`; no real secrets shared in chat or docs.
- [ ] Database (if any) is running and reachable.
- [ ] Seed or test data is available.
- [ ] The branch workflow is understood: branch from `main`, push, report.

## 3. Before accepting a contribution

- [ ] The report includes task IDs, branch name, files changed, and test steps.
- [ ] Only the assigned tasks were implemented.
- [ ] No unrelated refactors, renames, or formatting churn.
- [ ] Paths, methods, field names, types, and status codes match `docs/API_CONTRACT.md`.
- [ ] No endpoints, fields, or tables were invented.
- [ ] No secrets, `.env` files, tokens, or credentials in the diff.
- [ ] No `node_modules/`, `.venv/`, build output, or local database files committed.
- [ ] New dependencies are justified and recorded.
- [ ] Input validation and error handling exist where the task requires them.
- [ ] Loading, error, and empty states exist for new UI.
- [ ] No debug logs, commented-out code, or TODOs left behind.
- [ ] Shared documents (`docs/`, `AGENTS.md`, role files) were not edited by the developer.
- [ ] Branch is up to date with `main` and builds.
- [ ] Files use portable paths and work on both Windows and Linux.

## 4. Before merging

- [ ] You ran the build yourself on the branch — not just trusted the report.
- [ ] The app starts and the changed flow works end to end.
- [ ] Frontend calls match the backend implementation exactly (API compatibility).
- [ ] Database schema, migrations, and seed data match the contract (database compatibility).
- [ ] Every new environment variable is documented and present in `.env.example`.
- [ ] Dependencies install from a clean state.
- [ ] No duplicate components, endpoints, or utilities were introduced.
- [ ] CORS, ports, and base URLs are consistent between the two sides.
- [ ] The diff does not overwrite another developer's work.
- [ ] Conflicts were resolved deliberately, keeping both sides' intent.
- [ ] Nobody has pushed directly to `main` since the setup commit.
- [ ] Deployment configuration still valid (or updated in this change).

## 5. After merging

- [ ] `main` builds and starts.
- [ ] Core user flow works on `main` (smoke test, not a full regression).
- [ ] `docs/TASKS.md` statuses updated.
- [ ] All developers told to `git switch main && git pull origin main`.
- [ ] Feature branch deleted locally and on GitHub.
- [ ] Deployment (if automatic) succeeded; if manual, redeployed.
- [ ] Follow-up issues captured as new task IDs.
- [ ] New environment variables communicated to the team.

## 6. Before the final demo

- [ ] Demo runs from `main` (or the deployed build of `main`), not from a feature branch.
- [ ] `main` is deployed and the public URL works in a fresh browser or incognito window.
- [ ] Demo data is realistic and reset to a known-good state.
- [ ] The happy path works twice in a row.
- [ ] At least one error or empty state behaves gracefully.
- [ ] Production environment variables and API keys are set in the hosting platform.
- [ ] No console errors, debug banners, or placeholder text visible.
- [ ] Responsive layout checked at the screen size used for the demo.
- [ ] Presentation slides exist and match the shipped product.
- [ ] Demo script is timed and rehearsed by the person presenting.
- [ ] Fallback ready: screenshots or a short screen recording in case the live demo fails.
- [ ] Submission requirements completed (repository link, video, form, deadline).
- [ ] Feature freeze announced; nothing new merged after this point.
- [ ] Team knows who speaks, who drives the demo, and who handles questions.
- [ ] Devices charged; backup network available.
