"""Payment attempt model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(nullable=False)
    outcome: Mapped[str] = mapped_column(
        SAEnum("success", "failure", name="payment_outcome_enum"), nullable=False
    )
    failure_reason: Mapped[str | None] = mapped_column(nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="payment_attempts")

    def __repr__(self) -> str:
        return f"<PaymentAttempt(id={self.id}, outcome='{self.outcome}')>"


from app.models.invoice import Invoice  # noqa: E402, F401
