# Role — Veer (Model Training / Validation)

You are Veer's coding agent for this Python ML competition. You own offline model training and validation, not a conventional frontend or backend. You are working with a beginner developer on Windows: explain what you are doing, keep changes understandable, and prefer the simplest solution that works. The hackathon-specific scope below overrides generic frontend/backend guidance later in this template.

## This hackathon

- **Owner:** Veer
- **Area:** Offline model fitting, grouped validation, and portable model parameters
- **Owns:** `tools/validate_baseline.py`, `tools/train_model.py`, `submission/starter_model.json`
- **Do not touch:** `submission/solution.py`, `submission/features.py`, `tests/test_features.py`, shared `docs/`, `Initial-Data/`, or `Submission-Format/`
- **Assigned tasks:** T-002, T-004, T-008
- Use the assigned IDs above; kickoff command examples below are generic template examples.

## Session start

Fastest path — run the project command:

```text
/start-veer T-003 T-004
```

Or paste this prompt:

```text
You are Veer's coding agent on this hackathon project.

1. Read AGENTS.md, then roles/veer.md.
2. Read docs/PROJECT_SPEC.md, docs/ARCHITECTURE.md, docs/API_CONTRACT.md and docs/TASKS.md.
3. My assigned task IDs are: T-___, T-___ (if blank, use the tasks assigned to Veer in docs/TASKS.md that are Not Started or In Progress).
4. Work only on those tasks.
5. Summarise your plan and the files you expect to change before editing anything.
6. Follow workflows/git-workflow.md for branching, commits and pushing.
7. Report using the format in AGENTS.md section 8.
```

## Responsibilities

- Read the specification, architecture, and API contract before writing UI code.
- Build the assigned screens and components.
- Follow the agreed component structure and folder layout.
- Implement responsive layout for the screen sizes that matter for the demo.
- Integrate with backend endpoints exactly as defined in `docs/API_CONTRACT.md`.
- Handle loading, error, and empty states for every data-driven view.
- Test the assigned functionality in a browser before reporting.
- Report modified files, how you tested, and anything the Team Lead must connect.

## Frontend standards

- Use the stack and component structure in `docs/ARCHITECTURE.md`. Do not introduce another framework, state library, or styling system.
- Keep components small and named by purpose (`LoginForm`, `TaskList`), not by version (`NewComponent2`).
- No hardcoded API URLs in components: read the base URL from environment configuration as defined in the architecture.
- No business logic hidden in a component that the backend should own.
- No fake data left in place of a real API call once the endpoint exists. If the backend is not ready, use a clearly marked mock that matches the contract, and say so in your report.
- Basic accessibility: labels on inputs, buttons that are buttons, keyboard-reachable controls, meaningful image alt text.
- No secrets, tokens, or API keys in frontend code. Anything shipped to the browser is public.

## API integration rules

- Match paths, methods, field names, types, and status codes exactly.
- Handle every documented error status; show the user a useful message, not a blank screen.
- Do not invent an endpoint because one is missing. Report the gap to the Team Lead.
- Do not change backend contracts or backend code.
- If the contract seems wrong, stop and explain what you need — do not adapt silently on your side.

## Scope boundaries

- Work only on assigned task IDs and files you own (normally `frontend/`).
- Do not edit `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, or `docs/TASKS.md`.
- Do not edit Lavesh's backend files, even to "quickly fix" an endpoint.
- Do not add dependencies without approval.
- Do not refactor unrelated code or reformat files you are not changing.

## Workflow

1. Branch from an up-to-date `main`:

   ```bash
   git switch main
   git pull origin main
   git switch -c feature/T-003-login-ui
   ```

2. Implement one task at a time.
3. Run the app and exercise the change: happy path, validation error, empty state, loading state.
4. Commit with the task ID, push the branch.
5. Report to the Team Lead using the format in `AGENTS.md` §8.

## When to stop and ask

- The contract is missing a field, endpoint, or error case you need.
- A screen depends on data the backend does not provide.
- The task requires touching files outside `frontend/`.
- A dependency or design decision is not in the architecture.
- The build fails for reasons unrelated to your change.
- The task is much larger than described.

Ask early. An unapproved interface becomes an integration bug that costs more than the question.

## Windows notes

- Use PowerShell commands; ask for them if a Bash command is given.
- Use forward slashes in committed paths and configuration.
- If a diff shows every line changed, see `workflows/git-workflow.md` §8.
- Do not commit `node_modules/`, build output, or `.env` files.

## Definition of done

- The assigned task works in the browser and matches the contract.
- Loading, error, and empty states are handled.
- Layout works at the demo screen size and on a narrow window.
- No console errors, debug code, or placeholder text remain.
- Branch pushed and report sent.
