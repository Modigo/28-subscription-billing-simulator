"""Plan change history model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlanChangeHistory(Base):
    __tablename__ = "plan_change_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False)
    old_plan_id: Mapped[int] = mapped_column(nullable=False)
    new_plan_id: Mapped[int] = mapped_column(nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    change_type: Mapped[str] = mapped_column(
        SAEnum("immediate", "next_cycle", name="plan_change_type_enum"),
        nullable=False,
        default="next_cycle",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subscription: Mapped["Subscription"] = relationship(back_populates="plan_changes")

    def __repr__(self) -> str:
        return f"<PlanChangeHistory(id={self.id}, type='{self.change_type}')>"


from app.models.subscription import Subscription  # noqa: E402, F401
