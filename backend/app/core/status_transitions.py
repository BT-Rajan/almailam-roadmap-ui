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
#
# "Signed" is deliberately still listed here as a Draft transition --
# contract_service.set_status still accepts it (that's what
# confirm_contract_signing calls) -- but the only way to actually reach
# it is staff uploading the client's physically signed copy (see
# ProjectContractTab.vue's SignedDocumentUploadDialog), same treatment
# as Quotation's "Approved". The frontend's own mirror of this table
# (CONTRACT_ALLOWED_TRANSITIONS in src/constants/
# quotationContractOptions.ts) omits it from Draft's manual "Change
# Status" options for that reason.
CONTRACT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Signed"},
    "Signed": {"Active"},
    "Active": {"Expired", "Terminated"},
    "Expired": {"Draft"},
    "Terminated": set(),
}
CONTRACT_STATUSES_REQUIRING_REASON = {"Terminated"}

# --- Tasks -- src/types/Task.ts: TaskStatus
#
# "Preset" (migration 0088) is the initial status for a system-generated
# service task -- reachable only by creation, never a manual target (no
# other state transitions back into it), so it isn't listed as a value
# in any *other* row's set below. task_service.update_task moves a
# Preset task to "Pending" itself the moment anything about it changes
# (owner, dates, ...), which is the normal, expected way out of it; the
# explicit transitions here (In Progress/Completed) cover a task
# skipping straight past a plain reassignment into real work or being
# closed immediately.
TASK_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Preset": {"Pending", "In Progress", "Completed"},
    "Pending": {"In Progress"},
    "In Progress": {"Completed", "Pending"},
    "Completed": {"In Progress"},
}
# Reopening a completed task is the one task transition worth a paper
# trail; everything else is routine day-to-day movement.
TASK_STATUSES_REQUIRING_REASON: set[str] = set()

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
# "Supervision" (migration 0056) is an independent add-on stage -- a
# project can include Design, Government Submission (Permits),
# Supervision, any combination, or none (see
# project_service.compute_stage_flags).
#
# "Payment Plan" (migration 0061) sits between Quotation and Contract --
# the project's financial agreement(s) now have to be generated and
# explicitly approved before a contract is even drafted.
#
# Design/Government Submission/Supervision run in PARALLEL, not
# sequentially, as of migration 0089 (the "Handover" stage) -- Contract
# can be followed by any of the three (whichever this project actually
# includes; _auto_advance_target picks one arbitrarily as the initial
# landing spot, there's no real ordering), each of the three can move
# freely to either of the other two (a lateral "which track is
# currently focused" pointer, not a real gate -- staff can already work
# any of them regardless of current_stage via the stepper), and all
# three lead to Handover, the new terminal stage where the client's
# hand-over is actually confirmed. This table is deliberately the
# permissive superset of every structurally possible edge; whether a
# given project is actually allowed into "Design"/"Government
# Submission"/"Supervision" specifically (i.e. whether it includes that
# kind of work at all), and whether every included track is actually
# done before Handover, is enforced separately, in
# project_service._assert_stage_exit_criteria.
PROJECT_STAGE_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Requirement": {"Quotation"},
    "Quotation": {"Payment Plan"},
    "Payment Plan": {"Contract"},
    "Contract": {"Design", "Government Submission", "Supervision"},
    "Design": {"Government Submission", "Supervision", "Handover"},
    "Government Submission": {"Design", "Supervision", "Handover"},
    "Supervision": {"Design", "Government Submission", "Handover"},
    # The one reopening path out of Handover -- back to any of the three
    # parallel tracks, in case something turns up after convergence that
    # needs redoing. Requires a reason (see project_service.set_stage,
    # not the target-only REQUIRING_REASON table below, since Design/
    # Government Submission/Supervision are also each other's normal,
    # reason-free lateral targets and REQUIRING_REASON can't tell "from
    # Handover" apart from "from a peer track").
    "Handover": {"Design", "Government Submission", "Supervision"},
}
PROJECT_STAGE_STATUSES_REQUIRING_REASON: set[str] = set()

# --- Financial Agreement (the "payment plan") -- src/types/Payment.ts:
# FinancialAgreement.status
#
# Added alongside "Payment Plan" becoming a real workflow stage
# (migration 0061) -- a freshly-created agreement is a Draft (its
# obligations/schedule already exist, same as always, but it isn't yet
# what gates advancing the project) until explicitly Approved. Most
# post-approval corrections are a real Adjustment/Refund against the
# obligations, not a reopen back to Draft -- but neither of those can
# move a due_date or resize the schedule itself, so Approved -> Draft
# is allowed too, for the one thing they can't cover (see
# payment_service.reopen_agreement's own guard: only when no Payment
# has been recorded yet and the project has no Contract on file, same
# two conditions _assert_agreement_editable already requires for a
# plain edit). Requires a reason, since undoing an approval is
# significant enough to want one on the record.
FINANCIAL_AGREEMENT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Approved"},
    "Approved": {"Draft"},
}
FINANCIAL_AGREEMENT_STATUSES_REQUIRING_REASON: set[str] = {"Draft"}

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
    # "Completed" is only ever reached via project_service.
    # confirm_project_handover (the client's signed hand-over
    # acknowledgment), not a manual status change -- it's still listed
    # here (rather than bypassing assert_transition_allowed) so that
    # path goes through the same validation/audit-logging every other
    # status change does.
    # No transition out of "Completed" -- there's no reopen path yet.
    "Active": {"On Hold", "Cancelled", "Completed"},
    "On Hold": {"Active", "Cancelled"},
    "Cancelled": {"Active"},
    "Completed": set(),
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
