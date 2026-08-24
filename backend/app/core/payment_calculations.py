"""Direct port of src/utils/paymentHelpers.ts. Kept as pure functions with
no DB access (like core/workflow.py) so the same rules the frontend
already implements can be tested and trusted in isolation.
"""

from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal

FREQUENCY_INTERVAL_MONTHS = {
    "Monthly": 1,
    "Quarterly": 3,
    "Half-yearly": 6,
    "Yearly": 12,
}


def compute_obligation_status(obligation, today: date | None = None) -> str:
    """'Cancelled' and 'Waived' are manual overrides and always win."""
    if obligation.manual_status:
        return obligation.manual_status

    today = today or date.today()
    is_past_due = obligation.due_date < today
    is_due_today = obligation.due_date == today
    is_fully_paid = obligation.amount_received >= obligation.amount_due
    is_partially_paid = 0 < obligation.amount_received < obligation.amount_due

    if is_fully_paid:
        return "Paid"
    if is_partially_paid:
        return "Partially Overdue" if is_past_due else "Partially Paid"
    if is_past_due:
        return "Overdue"
    if is_due_today:
        return "Due"
    return "Scheduled"


def get_obligation_amount_pending(obligation) -> Decimal:
    return max(Decimal("0"), Decimal(str(obligation.amount_due)) - Decimal(str(obligation.amount_received)))


def get_obligation_amount_overdue(obligation, today: date | None = None) -> Decimal:
    status = compute_obligation_status(obligation, today)
    if status in ("Overdue", "Partially Overdue"):
        return get_obligation_amount_pending(obligation)
    return Decimal("0")


def get_next_payment_obligation(obligations: list, today: date | None = None):
    """The earliest (by sequence number) obligation that isn't fully
    settled and isn't cancelled/waived -- an obligation further down the
    schedule must never show as 'next' while an earlier one is unpaid."""
    for obligation in sorted(obligations, key=lambda o: o.sequence_number):
        status = compute_obligation_status(obligation, today)
        if status not in ("Paid", "Cancelled", "Waived"):
            return obligation
    return None


def get_days_until_due(due_date: date, today: date | None = None) -> int:
    today = today or date.today()
    return (due_date - today).days


def get_financial_summary(
    agreement, obligations: list, payments: list | None = None, refunds: list | None = None
) -> dict:
    today = date.today()
    active_obligations = [o for o in obligations if o.manual_status not in ("Cancelled", "Waived")]

    total_overdue = sum(
        (get_obligation_amount_overdue(o, today) for o in active_obligations), Decimal("0")
    )

    # A waived/cancelled obligation's un-received balance is money the
    # contract said was payable but that will never be collected --
    # excluded from Total Pending (see active_obligations above), but it
    # still needs to be accounted for somewhere so Contract Value stays
    # reconciled to Received + Pending + Overdue + Waived + Cancelled
    # instead of just silently vanishing.
    total_waived = sum(
        (get_obligation_amount_pending(o) for o in obligations if o.manual_status == "Waived"), Decimal("0")
    )
    total_cancelled = sum(
        (get_obligation_amount_pending(o) for o in obligations if o.manual_status == "Cancelled"), Decimal("0")
    )

    if payments is None:
        # Per-obligation ledger view -- correct as long as every payment
        # was fully allocated to an obligation when recorded.
        #
        # Pending and overdue are mutually exclusive: once an obligation's
        # due date passes, its outstanding balance moves out of Total
        # Pending and into Total Overdue rather than being counted in both.
        total_received = sum((Decimal(str(o.amount_received)) for o in obligations), Decimal("0"))
        total_pending = sum(
            (
                get_obligation_amount_pending(o)
                for o in active_obligations
                if compute_obligation_status(o, today) not in ("Overdue", "Partially Overdue")
            ),
            Decimal("0"),
        )
    else:
        # Actual-money view: total received is what payments actually
        # recorded, not what got allocated to an obligation row -- a
        # payment can be recorded for the full amount due while an
        # allocation mistake (or a payment made before its obligation
        # existed) leaves an obligation's own amount_received short.
        #
        # Total payable is the agreement's own contract_amount -- NOT
        # sum(obligation.amount_due). Those two are supposed to match
        # (an even schedule is generated to sum exactly to
        # contract_amount, see generate_even_schedule), but 'One-time'
        # and 'Custom' schedules are entered by hand and nothing
        # enforces that they reconcile against the contract value, so
        # obligations can drift from what the agreement actually says is
        # payable (an extra or mis-entered obligation row inflates the
        # sum without the contract itself changing). contract_amount is
        # the number the UI calls "Contract Value" and the one Total
        # Pending has to reconcile against, so it's the anchor here, not
        # a derived sum that can silently disagree with it.
        #
        # Rounded down to whole currency units so a fils-level rounding
        # remainder (the same schedule generation's remainder-folding)
        # never reads as still outstanding once the real money is all
        # in.
        #
        # total_overdue is subtracted out here too, for the same reason as
        # the ledger view above: once an obligation crosses its due date,
        # its balance belongs to Total Overdue, not Total Pending.
        #
        # The anchor is contract_amount minus whatever's been waived or
        # cancelled -- not raw contract_amount -- for the same reason the
        # ledger view excludes those obligations from total_pending: a
        # waived/cancelled balance is no longer part of what's actually
        # still payable.
        #
        # total_received also nets out refunds: a refund only ever
        # touches the obligation ledger's amount_received today, never
        # the original Payment row, so without this a refunded amount
        # would still read as received here even though the money went
        # back out.
        total_payable = Decimal(str(agreement.contract_amount)) - total_waived - total_cancelled
        gross_received = sum((Decimal(str(p.amount_received)) for p in payments), Decimal("0"))
        total_refunded = sum((Decimal(str(r.refund_amount)) for r in (refunds or ())), Decimal("0"))
        total_received = gross_received - total_refunded
        outstanding = (total_payable - total_received - total_overdue).quantize(Decimal("1"), rounding=ROUND_DOWN)
        total_pending = max(Decimal("0"), outstanding)

    next_obligation = get_next_payment_obligation(obligations, today)
    days_until_due = get_days_until_due(next_obligation.due_date, today) if next_obligation else None
    is_overdue = days_until_due is not None and days_until_due < 0

    # Should normally be zero -- nonzero only means an Adjustment has
    # moved obligation amounts without a matching change to
    # contract_amount, so the schedule and the contract have drifted
    # apart. Surfaced rather than silently absorbed either way.
    schedule_variance = Decimal(str(agreement.contract_amount)) - (
        total_received + total_pending + total_overdue + total_waived + total_cancelled
    )

    return {
        "contractAmount": agreement.contract_amount,
        "totalReceived": total_received,
        "totalPending": total_pending,
        "totalOverdue": total_overdue,
        "totalWaived": total_waived,
        "totalCancelled": total_cancelled,
        "scheduleVariance": schedule_variance,
        "nextPaymentObligation": next_obligation,
        "nextPaymentDaysUntilDue": days_until_due,
        "nextPaymentIsOverdue": is_overdue,
    }


def generate_even_schedule(
    contract_amount: Decimal, contract_start_date: date, contract_end_date: date | None, payment_frequency: str
) -> list[dict]:
    """'One-time' and 'Custom' schedules are created directly by the user
    instead (a custom schedule doesn't fit an even split)."""
    if payment_frequency == "One-time":
        return [
            {"sequenceNumber": 1, "description": "Full payment", "amountDue": contract_amount, "dueDate": contract_start_date}
        ]

    interval_months = FREQUENCY_INTERVAL_MONTHS.get(payment_frequency)
    if not interval_months or not contract_end_date:
        return [
            {"sequenceNumber": 1, "description": "Full payment", "amountDue": contract_amount, "dueDate": contract_start_date}
        ]

    installments: list[dict] = []
    cursor = contract_start_date
    sequence_number = 1
    while cursor <= contract_end_date:
        installments.append(
            {"sequenceNumber": sequence_number, "description": f"Installment {sequence_number}", "dueDate": cursor}
        )
        cursor = _add_months(cursor, interval_months)
        sequence_number += 1

    if not installments:
        return [
            {"sequenceNumber": 1, "description": "Full payment", "amountDue": contract_amount, "dueDate": contract_start_date}
        ]

    # Split evenly, folding any rounding remainder into the final
    # installment so the schedule always sums exactly to the contract
    # amount (avoids under/over-collecting by a few cents).
    count = len(installments)
    base_amount = (contract_amount / count).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    remainder = (contract_amount - base_amount * count).quantize(Decimal("0.01"))

    for index, installment in enumerate(installments):
        installment["amountDue"] = base_amount + remainder if index == count - 1 else base_amount

    return installments


def _add_months(source_date: date, months: int) -> date:
    month_index = source_date.month - 1 + months
    year = source_date.year + month_index // 12
    month = month_index % 12 + 1
    # Clamp the day for months with fewer days (e.g. Jan 31 + 1 month -> Feb 28/29).
    day = min(source_date.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - timedelta(days=1)).day
