from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Enum,
)
from sqlalchemy.orm import relationship

from database import Base


class SubStatus(PyEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    CANCELED = "cancelled"
    SUSPENDED = "suspended"


class InvoiceStatus(PyEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    RETRYING = "retrying"
    SUSPENDED = "suspended"


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    subscriptions = relationship(
        "Subscription",
        back_populates="plan",
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    customer_name = Column(String(150), nullable=False)

    plan_id = Column(
        Integer,
        ForeignKey("plans.id"),
        nullable=False,
    )

    status = Column(
        Enum(
            SubStatus,
            native_enum=False,
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
        ),
        default=SubStatus.ACTIVE,
        nullable=False,
    )

    next_billing_date = Column(DateTime, nullable=True)

    plan = relationship(
        "Plan",
        back_populates="subscriptions",
    )

    invoices = relationship(
        "Invoice",
        back_populates="subscription",
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id"),
        nullable=False,
    )

    customer_name = Column(String(150), nullable=False)

    amount_due = Column(Numeric(10, 2), nullable=False)

    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    status = Column(
        Enum(
            InvoiceStatus,
            native_enum=False,
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
        ),
        default=InvoiceStatus.PENDING,
        nullable=False,
    )

    next_retry_date = Column(DateTime, nullable=True)

    payment_failed_at = Column(DateTime, nullable=True)

    subscription = relationship(
        "Subscription",
        back_populates="invoices",
    )

    dunning_logs = relationship(
        "DunningLog",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class DunningLog(Base):
    __tablename__ = "dunning_logs"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False,
    )

    attempt_number = Column(Integer, nullable=False)

    execution_date = Column(DateTime, nullable=False)

    log_message = Column(String(500), nullable=False)

    invoice = relationship(
        "Invoice",
        back_populates="dunning_logs",
    )
