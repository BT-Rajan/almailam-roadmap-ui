"""Each table below mirrors one of the frontend's real status enums
exactly (see the referenced type file) -- these are ready for the
entity passes (B08-B12) to import once those models/routes exist.
Nothing in this file talks to a database; it's pure state-machine data
plus the reason-required set for each entity, consumed via
core/workflow.assert_transition_allowed / assert_reason_given.
"""

# --- Government Submissions -- src/types/Submission.ts: SubmissionStatus
SUBMISSION_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Submitted", "Withdrawn"},
    "Submitted": {"Under Review", "Withdrawn"},
    "Under Review": {"Comments Received", "Approved", "Rejected", "Withdrawn"},
    "Comments Received": {"Submitted", "Under Review", "Rejected", "Withdrawn"},
    "Approved": set(),
    "Rejected": {"Draft"},
    "Withdrawn": set(),
}
SUBMISSION_STATUSES_REQUIRING_REASON = {"Rejected", "Comments Received", "Withdrawn"}

# --- Quotations -- src/types/Quotation.ts: QuotationStatus
#
# "Sent" was removed (migration 0035) -- it was a pure intermediate
# value with no attached behavior (no email, no notification, nothing
# else in the app keyed off it), just one value in the generic status
# picklist. Draft now transitions directly to the same outcomes it used
# to reach only via Sent.
QUOTATION_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Approved", "Rejected", "Expired"},
    "Approved": set(),
    "Rejected": {"Draft"},
    "Expired": {"Draft"},
}
QUOTATION_STATUSES_REQUIRING_REASON = {"Rejected"}

# --- Contracts -- src/types/Contract.ts: ContractStatus
#
# "Sent" was removed (migration 0035), same reasoning as quotations
# above. Draft now transitions directly to Signed. Contracts do lose
# their one pre-signing correction path (Sent -> Draft) as a result --
# accepted, since nothing was ever attached to "Sent" for it to have
# been guarding.
CONTRACT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Signed"},
    "Signed": {"Active"},
    "Active": {"Expired", "Terminated"},
    "Expired": {"Draft"},
    "Terminated": set(),
}
CONTRACT_STATUSES_REQUIRING_REASON = {"Terminated"}

# --- Tasks -- src/types/Task.ts: TaskStatus
TASK_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Pending": {"In Progress"},
    "In Progress": {"Completed", "Pending"},
    "Completed": {"In Progress"},
}
# Reopening a completed task is the one task transition worth a paper
# trail; everything else is routine day-to-day movement.
TASK_STATUSES_REQUIRING_REASON: set[str] = set()

# --- Client Onboarding -- src/types/Client.ts: ClientOnboardingState
#
# Added here while building Pass B07 (the Client entity) -- B04's
# original scope only covered submissions/quotations/contracts/tasks/
# payment overrides and didn't anticipate this one, but it's the same
# mechanism and belongs in the same table of tables.
#
# "Verification Required" was removed as its own state: onboarding
# completeness is now judged on Identification and Consent being on
# file (see clientHelpers.ts's calculateOnboardingState), not on
# document verification, so "Documents Required" now moves straight to
# "Under Review". Document verification itself is unaffected -- it's
# still recorded per-document, it just no longer gates onboarding.
CLIENT_ONBOARDING_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Information Required": {"Documents Required"},
    "Documents Required": {"Under Review"},
    "Under Review": {"Ready", "Rejected", "Documents Required"},
    "Ready": {"Suspended"},
    "Suspended": {"Under Review", "Rejected"},
    "Rejected": {"Information Required"},
}
CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON = {"Rejected", "Suspended"}

# --- Project Workflow Stage -- src/types/Project.ts: WorkflowStage
#
# Same story as client onboarding above: discovered while building the
# Project entity in Pass B07, not anticipated by B04's original scope.
#
# "Correction" used to be its own stage here (Review <-> Correction, a
# loop back and forth with a required reason on the way into
# Correction) -- merged into a single "Review" stage (migration 0019):
# a document/submission sent back for fixes during review is still,
# functionally, "under review", and the stage hop wasn't preserving
# anything a reason-carrying project timeline note doesn't already
# capture. See timeline_service.create_event -- staff log a correction
# cycle as a reason-carrying note there now instead of moving the
# project's stage back and forth.
#
# "Review"/"Execution & Tracking" and "Completed" (added in migration
# 0022) were removed entirely in migration 0051 -- Government
# Submission is now the last stage, with no further stage to advance
# into.
#
# "Supervision" (migration 0056) sits alongside "Design" -- a project
# can include either, both, or neither (see
# project_service.compute_stage_flags), so Contract can be followed
# directly by Design, Supervision, or Government Submission, and Design
# can be followed by either Supervision or Government Submission. This
# table is deliberately the permissive superset of every structurally
# possible edge; whether a given project is actually allowed into
# "Design"/"Supervision" specifically (i.e. whether it includes that
# kind of work at all) is enforced separately, in
# project_service._assert_stage_exit_criteria.
PROJECT_STAGE_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Requirement": {"Quotation"},
    "Quotation": {"Contract"},
    "Contract": {"Design", "Supervision", "Government Submission"},
    "Design": {"Supervision", "Government Submission"},
    "Supervision": {"Government Submission"},
    # The reopening paths backward -- an authority's feedback during
    # Government Submission can require design or supervision changes,
    # so this needs somewhere to go back to. Requires a reason (see
    # PROJECT_STAGE_STATUSES_REQUIRING_REASON below), unlike the normal
    # forward flow, since it's a correction, not the default path.
    "Government Submission": {"Design", "Supervision"},
}
PROJECT_STAGE_STATUSES_REQUIRING_REASON: set[str] = set()

# --- Project Status -- src/types/Project.ts: ProjectStatus
#
# "Cancelled" is a true dead end -- added a path back to "Active" rather
# than leaving no recovery at all. Unlike "On Hold" -> "Active" (a
# routine, frequent, reason-free resume), reopening a Cancelled project
# is exceptional -- enforced directly in project_service.set_status()
# rather than here, since REQUIRING_REASON only keys on the target
# state. "Completed" was removed entirely in migration 0051, along with
# the workflow stage of the same name it used to require current_stage
# to have also reached.
PROJECT_STATUS_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Active": {"On Hold", "Cancelled"},
    "On Hold": {"Active", "Cancelled"},
    "Cancelled": {"Active"},
}
PROJECT_STATUS_STATUSES_REQUIRING_REASON = {"On Hold", "Cancelled"}

# --- Document Status -- src/types/Document.ts: DocumentStatus
#
# Same story as the client onboarding / project stage / status tables
# above: discovered while building the Document entity in Pass B11.
DOCUMENT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Under Review"},
    "Under Review": {"Approved", "Rejected"},
    "Approved": set(),
    "Rejected": {"Draft"},
}
DOCUMENT_STATUSES_REQUIRING_REASON = {"Rejected"}

# --- Payment Obligations -- src/types/Payment.ts: PaymentObligation.manualStatus
#
# IMPORTANT: this is NOT the 8-value ObligationStatus shown in the UI
# (Scheduled/Due/Paid/Overdue/...) -- that whole display status is
# computed live from amountDue/amountReceived/dueDate by
# utils/paymentHelpers.computeObligationStatus() and is never set
# directly. The only thing an operator actually *transitions* is
# whether a manual override is in effect. "Computed" here is a
# sentinel meaning manualStatus is unset, i.e. let the live
# calculation drive the displayed status.
OBLIGATION_OVERRIDE_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Computed": {"Cancelled", "Waived"},
    "Cancelled": {"Computed", "Waived"},
    "Waived": {"Computed", "Cancelled"},
}
OBLIGATION_OVERRIDE_STATUSES_REQUIRING_REASON = {"Cancelled", "Waived"}
