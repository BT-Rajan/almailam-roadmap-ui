# e2e-workflow -- modulewise workflow verification

A separate e2e stream from `e2e/` and `playwright.config.ts`. It exists
to answer one question per module: **did what we sent actually land in
the database, and does the real workflow engine take it all the way
through to completion?**

It is one continuous story told across four numbered spec files, run
in order, against **one** tagged data set:

| File | Module | What it does |
|---|---|---|
| `01-client-creation.spec.ts` | Client Creation | Drives the real New Client wizard (UI), captures the exact `POST /api/clients/full` request, compares it to the DB row. |
| `02-project-creation.spec.ts` | Project Creation | Drives the real New Project wizard (UI) for that client, compares the `POST /api/projects` request to the DB row. |
| `03-project-workflow.spec.ts` | Project Workflow | Drives the backend API directly through Requirement → Quotation → Payment Plan → Contract → Design → Handover → Completed, asserting the DB's `current_stage`/`status` after every hop, then spot-checks the Project Workspace page (UI) shows the final state. |
| `04-reports.spec.ts` | Reports | Compares the `clients-projects` / `projects-by-status` / per-project report API responses to the DB, then spot-checks the Reports page (UI). |

## Why this is separate from `e2e/`

- **Different contract.** The existing `e2e/` suite is example-/scenario-driven. This suite is one linear pipeline where each file depends on the previous one's output -- it needs `workers: 1`, no `fullyParallel`, and a shared state file (`.artifacts/state.json`, see `helpers/state.ts`) to hand IDs (client ID → project number → quotation/agreement/contract numbers) from file to file. Mixing that into the main config would change how every other spec in `e2e/` runs.
- **Guaranteed cleanup.** `global-teardown.ts` always runs, pass or fail, and deletes every record this run created (see below). The main suite has no equivalent global teardown, and shouldn't need one.
- **A single tagged dataset.** Every record this suite creates is named/emailed with one run tag (e.g. `E2EVFY20260911143022`, see `global-setup.ts`) so it's instantly identifiable and impossible to confuse with real data -- and so cleanup can be scoped to *exactly* what this run created, never a broader query.

## Running it

You start the backend and DB yourself first (same as the main `e2e/` suite) -- this only launches the Vite dev server via Playwright's `webServer`.

```bash
npm run test:e2e:workflow
```

Environment variables (all optional):

| Variable | Default | Purpose |
|---|---|---|
| `E2E_API_BASE_URL` | `http://localhost:8000/api` | Backend base URL for Module 3/4's direct API calls. |
| `E2E_ADMIN_USER` | `admin` | Login username (UI and API). |
| `E2E_ADMIN_PASSWORD` | `Demo#2026` | Login password. |
| `E2E_PYTHON` | `python` | Python executable used to shell out to `backend/scripts/e2e_verify.py`. |

## How the DB comparison works

`backend/scripts/e2e_verify.py` is a small, standalone script (not part
of the app's normal request path) that reads the DB straight through
the app's own SQLAlchemy models:

```bash
python -m scripts.e2e_verify dump client 123
python -m scripts.e2e_verify dump project PRJ-2026-0042
python -m scripts.e2e_verify cleanup ../e2e-workflow/.artifacts/state.json
```

Each spec calls `dump` (via `helpers/dbVerify.ts`) after driving a UI
action or API call, and diffs the result against the actual request
payload it just sent -- so a passing assertion means the data really
reached the table, not just that two layers of the same service agree.

## Cleanup and isolation

Nothing in this suite ever queries or deletes by anything other than
the IDs it itself created and recorded in `.artifacts/state.json`.
`global-teardown.ts` runs unconditionally at the end of the suite (even
if a spec failed partway through) and deletes everything in the exact
order the schema's foreign keys require:

```
payments / refunds / adjustments (by ID)
  -> financial_agreements
  -> contract (RESTRICT on quotation_id)
  -> quotation
  -> project (RESTRICT on client_id; its own children -- selected
     activities/permits, scope revisions, timeline, handover checklist
     -- CASCADE automatically)
  -> client (its own children -- contacts, addresses, identifications
     -- CASCADE automatically)
```

Teardown fails loudly (rather than silently) if anything it expected to
delete is still there afterward. If a run is interrupted before
teardown runs (killed process, crashed suite), `.artifacts/state.json`
survives -- `global-setup.ts` refuses to start a new run on top of it
and tells you the exact `cleanup` command to run by hand first.

## Known scope limits

- Only the **Individual** client type and a **Design-only** project are
  exercised (Module 1 and 2's own comments explain why) -- the
  Organisation client branch and the Government Submission/Supervision
  tracks have their own exit criteria but aren't separately driven here.
- Module 3 drives the workflow via the backend API directly, not by
  clicking through the Quotation/Contract/Payment-Plan UI wizards --
  those are substantial forms in their own right, and the thing this
  module verifies is the workflow engine's transition rules, which are
  enforced identically regardless of caller.
- This is a first pass written from source, not yet run against a live
  stack in this environment (no DB/backend was available here). Expect
  to iterate on selectors/label text (`getByLabel`/`getByRole` calls) on
  the first real run -- see the inline comments in each spec for the
  source lines each selector was checked against.
