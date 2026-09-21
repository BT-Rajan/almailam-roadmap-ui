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

**Correction:** an earlier revision of this README claimed two additional
"confirmed" bugs here (a stale Scope panel on fresh page load of a project
past the Scope stage, and a New Project Wizard Supervision-activity date gap
causing a raw 422). Both were re-tested directly against the current code
(fresh `/projects/:id` loads at every stage; repeatedly checking a
Supervision activity in `ServicePickerDialog` with no dates set) and neither
reproduces — the workspace's Overview tab already renders the correct
stage-specific content on a fresh load, and `ServicePickerDialog`'s "Save
Selections" button is correctly disabled until every checked Supervision
activity has both a start and end date. The original observations were most
likely artifacts of the driver script's own rapid, scripted navigation
(e.g. a safety click the script made unconditionally, on an already-correct
tab) rather than real product bugs. Leaving this note rather than silently
deleting the claim.

What a second pass (static code review + live exploration of Admin, RBAC,
search, notifications, and form validation) did find and fix, on this branch:

- 4 vue-i18n message-compile crashes (bare `@`/`{{...}}` in placeholder
  strings in `administration.ts` locale files).
- A `watch(..., { immediate: true })` TDZ bug (self-referencing stop
  handle before its `const` finished initializing) in
  `ProjectQuotationTab.vue`, `PaymentPlanPanel.vue`, and
  `ProjectContractTab.vue`.
- Two dead "Try Again" buttons: `ErrorState`'s retry button always renders
  regardless of whether a `@retry` handler is bound, and
  `DocumentPreviewDialog.vue` / `ProjectDocumentsTab.vue` rendered it with
  none — clicking it silently did nothing. Both now retry the load that
  actually failed.
- A stale "(optional)" label on `ServicePickerDialog`'s per-activity
  Supervision end date field, which the code has required (with a red
  asterisk) since a past fix closed exactly this gap — the label just never
  caught up.
- A latent race in `projectStore`/`documentStore`/`clientStore`'s
  `load*Page()` actions: firing two overlapping requests (e.g. typing
  quickly in a filter) could let a slower, earlier response resolve after a
  faster later one and silently overwrite the list with stale, filter-
  mismatched results. Fixed with the same request-id guard `searchStore.ts`
  already used for its own search-as-you-type race.

Findings looked at and **not** changed (recommendations, not bugs, or
already handled elsewhere in the codebase): several disabled buttons across
the app (e.g. "New Contract", "Edit Scope", "Start Application") give no
on-hover explanation of *why* they're disabled — the codebase has no
tooltip primitive to hang that off yet, so fixing this well means adding
one, a small design decision rather than a bug fix. Also noted: most of the
Service Catalog's default services (Civil Engineering, Fire & Safety
Engineering, MEP Design, Structural Engineering) ship with zero priced
activities, so selecting them on a real project reproduces the same
KWD 0.00 quotation block project `2600002` demonstrates — a catalog/seed-
data gap, not a code bug.

## Regenerating

`drive.mjs` is committed as a record of what was run, not as a maintained
test suite — it references this session's scratchpad paths for its
state/screenshot/dummy-file locations and needs those constants updated to
re-run it elsewhere. It requires a working local dev stack (MySQL + backend
+ frontend) and the pre-installed Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`.
