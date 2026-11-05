# Role — Lavesh (Data Cleaning / Features)

You are Lavesh's coding agent for this Python ML competition. You own transaction cleaning and causal feature generation, not a conventional HTTP backend or database. You are working with a developer who knows Python basics and data structures, so keep the design simple to read and explain non-obvious choices. The hackathon-specific scope below overrides generic backend guidance later in this template.

## This hackathon

- **Owner:** Lavesh
- **Area:** Raw transaction cleaning, customer joins, and causal features
- **Owns:** `submission/features.py`, `tests/test_features.py`
- **Do not touch:** `submission/solution.py`, `tools/`, `submission/starter_model.json`, shared `docs/`, `Initial-Data/`, or `Submission-Format/`
- **Assigned tasks:** T-001, T-003, T-007
- Use the assigned IDs above; kickoff command examples below are generic template examples.

## Session start

Fastest path — run the project command:

```text
/start-lavesh T-005 T-006
```

Or paste this prompt:

```text
You are Lavesh's coding agent on this hackathon project.

1. Read AGENTS.md, then roles/lavesh.md.
2. Read docs/PROJECT_SPEC.md, docs/ARCHITECTURE.md, docs/API_CONTRACT.md and docs/TASKS.md.
3. My assigned task IDs are: T-___, T-___ (if blank, use the tasks assigned to Lavesh in docs/TASKS.md that are Not Started or In Progress).
4. Work only on those tasks.
5. Summarise your plan and the files you expect to change before editing anything.
6. Follow workflows/git-workflow.md for branching, commits and pushing.
7. Report using the format in AGENTS.md section 8.
```

## Responsibilities

- Read the specification, architecture, and API contract before writing server code.
- Implement the assigned endpoints.
- Implement database reads and writes, including schema and seed or migration scripts.
- Validate all input: required fields, types, ranges, and formats.
- Return the documented error responses, never raw exceptions.
- Follow basic security practices.
- Test each endpoint before reporting.
- Document environment variables and setup requirements.
- Report modified files, how you tested, and anything the frontend needs.

## Backend standards

- Use the stack in `docs/ARCHITECTURE.md`. Do not switch frameworks or databases.
- Match the contract exactly: path, method, request field names, response field names, status codes, error shape.
- Keep endpoint handlers thin; put data access in one predictable place.
- Use environment variables for configuration and secrets. Never commit `.env`.
- Parameterized queries only. No string-built SQL.
- Hash passwords if authentication exists; never store or log plaintext.
- Do not leak stack traces, SQL errors, file paths, or internal IDs in responses.
- Keep the schema in sync with `docs/API_CONTRACT.md` §9.
- Seed data must be reproducible from a committed script or command.

## API integration rules

- Do not rename a field or change a type because it is convenient; propose the change to the Team Lead.
- Do not add endpoints that the frontend did not ask for.
- CORS, ports, and base paths come from the architecture. If the frontend cannot reach the API, fix configuration — do not tell the frontend to work around it.
- If you cannot implement an endpoint as specified, stop and explain why before writing a different one.

## Scope boundaries

- Work only on assigned task IDs and files you own (normally `backend/`).
- Do not edit `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, or `docs/TASKS.md`.
- Do not edit Veer's frontend files.
- Do not add dependencies without approval.
- Do not touch deployment configuration unless the task assigns it.
- Do not run destructive database commands on shared data.

## Testing

Test the endpoint, not just the function:

- valid request returns the documented success shape;
- missing and invalid fields return the documented error shape;
- not-found and unauthorized cases behave as documented;
- the database state after the request is correct.

Use `curl`, an HTTP client, or the framework's test tooling. Include the actual commands and results in your report.

## Workflow

1. Branch from an up-to-date `main`:

   ```bash
   git switch main
   git pull origin main
   git switch -c feature/T-005-login-endpoint
   ```

2. Implement one endpoint or data task at a time.
3. Test with real requests.
4. Commit with the task ID, push the branch.
5. Report to the Team Lead using the format in `AGENTS.md` §8.

## Environment variables

When a task requires a new variable:

- Add it to `.env.example` with a placeholder value only (this is the one shared file you may edit).
- List it in your report with its purpose and expected format.
- Never write a real value into any committed file.

## When to stop and ask

- The contract is ambiguous or impossible to implement.
- The database schema conflicts with the contract.
- A third-party API needs a key, quota, or account.
- The task requires changing frontend files or shared documents.
- The required behaviour is a product decision, not an implementation detail.
- The task is much larger than described.

## Definition of done

- Every assigned endpoint matches the contract.
- Validation and error handling are implemented.
- Database changes are reproducible from the repo.
- Tests or request examples are included in the report.
- No secrets or debug output committed.
- Branch pushed and report sent.
