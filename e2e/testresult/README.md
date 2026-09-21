# E2E walkthrough: Scope → Handover → Report

Playwright walkthrough of the full ServiceOS project lifecycle against a local
dev instance (frontend on `:5173`, backend on `:8000`), driven end-to-end
through the real browser UI (not API calls). Screenshots are numbered in the
order they were taken; `drive.mjs` is the exact driver script used to produce
them.

## Flow covered

1. Login as `admin` (seeded dev credential, see repo `README.md`).
2. Create a user (Project Manager) and an engineer (Field Engineer) via
   Admin > User Management.
3. Create a client (ABC Trading Company) via the 4-step New Client wizard.
4. Create a project via the New Project Wizard.
5. Drive the project through all 6 lifecycle stages:
   **Scope → Quotation → Payment Plan → Contract → Design → Handover**,
   including quotation pricing/approval, payment plan approval, contract
   signing, completing linked design tasks, and confirming handover — each
   with a signed-document upload where required.
6. View the project's **Project Performance** report (`p2-project-report*`)
   and the global **Reports** hub (`global-reports-list`).

Screenshots `1-99` cover project `2600002` (a first project deliberately left
stuck at the Payment Plan stage — see bug notes below) and the shared
setup steps (login, user/client/engineer creation). Screenshots `59-119`
cover project `2600003`, which was driven all the way to a **Completed**
status with a 100% Project Performance report.

## Bugs found during this walkthrough

Two real, reproducible frontend bugs were found and are **not yet fixed**:

1. **Stale Scope panel on fresh page load.** Navigating directly to a project
   workspace that's already past the Scope stage renders the stale
   Scope-of-Work panel (disabled "Save & Proceed") under the "Overview" tab,
   even though the stage banner above it correctly shows the current stage.
   Clicking the current stage's own label in the stepper forces the correct
   panel to render. Likely the stage-panel component isn't syncing its
   initial active-tab state to the freshly-loaded `project.currentStage`.
   Screenshots named `*-project-workspace-scope.png` throughout this set are
   the repro (and the test script's workaround, `gotoWorkspace()`, is
   documented in `drive.mjs`).

2. **New Project Wizard: Supervision activities missing date fields.**
   Selecting a Supervision catalog item (e.g. "Weekly Site Visits") lets the
   user complete the wizard and click "Create Project", but the request
   fails with a raw 422 (`Input should be a valid date or datetime, input is
   too short`) because `selectedSupervisionActivities[].startDate`/`endDate`
   are sent as empty strings — the wizard UI never collects them. Worked
   around in this walkthrough by not selecting a Supervision item for
   project `2600003`.

Also fixed during this pass (separate commits on this branch):
- 4 vue-i18n message-compile crashes (bare `@`/`{{...}}` in placeholder
  strings in `administration.ts` locale files).
- A `watch(..., { immediate: true })` TDZ bug (self-referencing stop
  handle before its `const` finished initializing) in
  `ProjectQuotationTab.vue`, `PaymentPlanPanel.vue`, and
  `ProjectContractTab.vue`.

## Regenerating

`drive.mjs` is committed as a record of what was run, not as a maintained
test suite — it references this session's scratchpad paths for its
state/screenshot/dummy-file locations and needs those constants updated to
re-run it elsewhere. It requires a working local dev stack (MySQL + backend
+ frontend) and the pre-installed Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.
