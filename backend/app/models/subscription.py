"""Subscription model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(
            "trialing", "active", "past_due", "suspended", "canceled", "paused",
            name="subscription_status_enum"
        ),
        nullable=False,
    )
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    trial_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="subscription", lazy="selectin"
    )
    plan_changes: Mapped[list["PlanChangeHistory"]] = relationship(
        back_populates="subscription", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, status='{self.status}')>"


from app.models.customer import Customer  # noqa: E402, F401
from app.models.plan import Plan  # noqa: E402, F401
from app.models.invoice import Invoice  # noqa: E402, F401
from app.models.plan_change import PlanChangeHistory  # noqa: E402, F401
