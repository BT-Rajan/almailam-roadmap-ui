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
QUOTATION_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Sent"},
    "Sent": {"Approved", "Rejected", "Expired"},
    "Approved": set(),
    "Rejected": {"Draft"},
    "Expired": {"Draft"},
}
QUOTATION_STATUSES_REQUIRING_REASON = {"Rejected"}

# --- Contracts -- src/types/Contract.ts: ContractStatus
CONTRACT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Sent"},
    "Sent": {"Signed", "Draft"},
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
CLIENT_ONBOARDING_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Information Required": {"Documents Required"},
    "Documents Required": {"Verification Required"},
    "Verification Required": {"Under Review"},
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
# "Completed" was originally a true dead end with no way back -- a
# project marked complete by mistake had no recovery path at all. Added
# a single escape hatch back to "Approval" (the stage immediately
# before) rather than opening up arbitrary backward jumps through the
# whole pipeline, which is a real stage-gate process with its own
# intentional structure. Unlike "Review" -> "Approval" (the normal,
# frequent, reason-free outcome of a successful review), reopening a
# Completed project is exceptional and source-dependent -- enforced
# directly in project_service.set_stage() rather than here, since
# REQUIRING_REASON only keys on the target state.
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
PROJECT_STAGE_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Enquiry": {"Quotation"},
    "Quotation": {"Contract"},
    "Contract": {"Design"},
    "Design": {"Government Submission"},
    "Government Submission": {"Review"},
    "Review": {"Approval"},
    "Approval": {"Completed"},
    "Completed": {"Approval"},
}
PROJECT_STAGE_STATUSES_REQUIRING_REASON: set[str] = set()

# --- Project Status -- src/types/Project.ts: ProjectStatus
#
# "Completed" and "Cancelled" were both true dead ends too -- same
# reasoning as above, added a path back to "Active" for each rather than
# leaving no recovery at all. Unlike "On Hold" -> "Active" (a routine,
# frequent, reason-free resume), reopening a Completed or Cancelled
# project is exceptional -- that reason requirement is source-dependent
# (only when recovering FROM one of those two, not from "On Hold"), so
# it's enforced directly in project_service.set_status() rather than
# here, since REQUIRING_REASON only keys on the target state. Moving
# status to "Completed" additionally requires current_stage to already
# be "Completed" too (also enforced in set_status(), not here) so the
# two parallel fields can't silently disagree with each other.
PROJECT_STATUS_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Active": {"On Hold", "Completed", "Cancelled"},
    "On Hold": {"Active", "Cancelled"},
    "Completed": {"Active"},
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
