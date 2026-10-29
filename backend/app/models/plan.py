"""Plan model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(default="NGN", nullable=False)
    billing_interval: Mapped[str] = mapped_column(
        SAEnum("monthly", "yearly", name="billing_interval_enum"), nullable=False
    )
    trial_days: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("active", "retired", name="plan_status_enum"), default="active", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, name='{self.name}', price={self.price})>"


from app.models.subscription import Subscription  # noqa: E402, F401
