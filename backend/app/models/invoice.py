"""Invoice model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        # Idempotency: one invoice per subscription per billing period
        UniqueConstraint("subscription_id", "billing_period_start", name="uq_subscription_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "paid", "failed", "void", name="invoice_status_enum"),
        nullable=False,
        default="pending",
    )
    billing_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    billing_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Snapshot of plan details at invoice time
    plan_name: Mapped[str | None] = mapped_column(nullable=True)
    plan_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subscription: Mapped["Subscription"] = relationship(back_populates="invoices")
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(
        back_populates="invoice", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', status='{self.status}')>"


from app.models.subscription import Subscription  # noqa: E402, F401
from app.models.payment_attempt import PaymentAttempt  # noqa: E402, F401
