from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK

PAYMENT_MODES = ("Cash", "Bank Transfer", "Credit Card", "Debit Card", "Online Payment", "Cheque", "Other")
PAYMENT_FREQUENCIES = ("One-time", "Daily", "Weekly", "Monthly", "Quarterly", "Half-yearly", "Yearly", "Custom")
OBLIGATION_MANUAL_STATUSES = ("Cancelled", "Waived")
ADJUSTMENT_TYPES = ("Increase", "Decrease", "Correction")
AGREEMENT_STREAMS = ("Design", "Supervision")


class FinancialAgreement(Base):
    __tablename__ = "financial_agreements"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Which billing stream this agreement covers (migration 0059) -- a
    # project can have one Design (one-time) agreement and one
    # Supervision (monthly, day-prorated) agreement side by side, hence
    # the (project_id, stream) unique constraint rather than the old
    # one-per-project rule.
    stream: Mapped[str] = mapped_column(Enum(*AGREEMENT_STREAMS, name="agreement_stream"), nullable=False, default="Design")
    contract_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="KWD")
    contract_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    contract_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    agreement_date: Mapped[date] = mapped_column(Date, nullable=False)
    quotation_reference: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contract_reference: Mapped[str | None] = mapped_column(String(30), nullable=True)
    payment_mode: Mapped[str] = mapped_column(Enum(*PAYMENT_MODES, name="agreement_payment_mode"), nullable=False)
    payment_frequency: Mapped[str] = mapped_column(
        Enum(*PAYMENT_FREQUENCIES, name="payment_frequency"), nullable=False
    )


class PaymentObligation(Base):
    __tablename__ = "payment_obligations"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    agreement_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("financial_agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_due: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_received: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    manual_status: Mapped[str | None] = mapped_column(
        Enum(*OBLIGATION_MANUAL_STATUSES, name="obligation_manual_status"), nullable=True
    )
    # Set once, the first time a payment brings amount_received up to
    # amount_due -- denormalized "how this was ultimately settled"
    # convenience fields, taken from that settling payment.
    date_paid: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(
        Enum(*PAYMENT_MODES, name="obligation_payment_method"), nullable=True
    )
    reference_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Idempotency guards for the daily payment-reminder job (see
    # payment_service.check_and_notify_payment_reminders) -- one per
    # reminder point so each fires exactly once. No "stop" flag is
    # needed: date_paid being set is itself "payment confirmation has
    # arrived" and the job simply excludes settled obligations.
    reminder_before_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reminder_due_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reminder_after_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    agreement_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("financial_agreements.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    amount_received: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_mode: Mapped[str] = mapped_column(Enum(*PAYMENT_MODES, name="payment_mode"), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    payer: Mapped[str] = mapped_column(String(150), nullable=False)
    receiving_account: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    obligation_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("payment_obligations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount_allocated: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    payment_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    agreement_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("financial_agreements.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    obligation_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("payment_obligations.id", ondelete="RESTRICT"), nullable=False
    )
    refund_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    refund_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorising_user: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reference: Mapped[str | None] = mapped_column(String(60), nullable=True)


class Adjustment(Base):
    __tablename__ = "adjustments"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    agreement_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("financial_agreements.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    obligation_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("payment_obligations.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[str] = mapped_column(Enum(*ADJUSTMENT_TYPES, name="adjustment_type"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorising_user: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    adjusted_at: Mapped[date] = mapped_column(Date, nullable=False)
