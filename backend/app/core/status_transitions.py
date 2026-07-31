"""Each table below mirrors one of the frontend's real status enums
exactly (see the referenced type file) -- these are ready for the
entity passes (B08-B12) to import once those models/routes exist.
Nothing in this file talks to a database; it's pure state-machine data
plus the reason-required set for each entity, consumed via
core/workflow.assert_transition_allowed / assert_reason_given.
"""

# --- Government Submissions -- src/types/Submission.ts: SubmissionStatus
SUBMISSION_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Submitted"},
    "Submitted": {"Under Review"},
    "Under Review": {"Comments Received", "Approved", "Rejected"},
    "Comments Received": {"Submitted", "Under Review", "Rejected"},
    "Approved": set(),
    "Rejected": {"Draft"},
}
SUBMISSION_STATUSES_REQUIRING_REASON = {"Rejected", "Comments Received"}

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
