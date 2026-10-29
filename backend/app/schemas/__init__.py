"""Pydantic schemas for all API request/response types."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ─── Customer ────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerDetailResponse(CustomerResponse):
    subscriptions: list["SubscriptionResponse"] = []


# ─── Plan ────────────────────────────────────────────────────────────────────

class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0)
    currency: str = Field(default="NGN", min_length=3, max_length=3)
    billing_interval: str = Field(default="monthly")
    trial_days: int = Field(default=0, ge=0)

    @field_validator("billing_interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        if v not in ("monthly", "yearly"):
            raise ValueError("billing_interval must be 'monthly' or 'yearly'")
        return v


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_interval: str | None = None
    trial_days: int | None = Field(default=None, ge=0)


class PlanResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    currency: str
    billing_interval: str
    trial_days: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Subscription ────────────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int


class SubscriptionChangePlan(BaseModel):
    plan_id: int
    change_type: str = Field(default="next_cycle")

    @field_validator("change_type")
    @classmethod
    def validate_change_type(cls, v: str) -> str:
        if v not in ("immediate", "next_cycle"):
            raise ValueError("change_type must be 'immediate' or 'next_cycle'")
        return v


class SubscriptionResponse(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    status: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: datetime | None
    canceled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    plan: PlanResponse | None = None
    customer: CustomerResponse | None = None

    model_config = {"from_attributes": True}


# ─── Invoice ─────────────────────────────────────────────────────────────────

class InvoiceResponse(BaseModel):
    id: int
    subscription_id: int
    invoice_number: str
    amount: Decimal
    currency: str
    status: str
    billing_period_start: datetime
    billing_period_end: datetime
    issued_at: datetime
    due_at: datetime
    paid_at: datetime | None
    attempt_count: int
    next_retry_at: datetime | None
    plan_name: str | None
    plan_price: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int


# ─── Payment Attempt ─────────────────────────────────────────────────────────

class PaymentAttemptResponse(BaseModel):
    id: int
    invoice_id: int
    attempt_number: int
    outcome: str
    failure_reason: str | None
    attempted_at: datetime

    model_config = {"from_attributes": True}


class SimulatePaymentRequest(BaseModel):
    outcome: str = Field(default="success")

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        if v not in ("success", "failure"):
            raise ValueError("outcome must be 'success' or 'failure'")
        return v


# ─── Billing Event ───────────────────────────────────────────────────────────

class BillingEventResponse(BaseModel):
    id: int
    event_type: str
    subscription_id: int | None
    invoice_id: int | None
    details: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_customers: int
    total_active_subscriptions: int
    total_invoices: int
    paid_invoices: int
    failed_invoices: int
    past_due_subscriptions: int
    suspended_subscriptions: int
    total_revenue: dict[str, Decimal]  # currency -> amount
    recent_invoices: list[InvoiceResponse] = []
    recent_events: list[BillingEventResponse] = []


# ─── Billing Operations ──────────────────────────────────────────────────────

class BillingRunResult(BaseModel):
    processed: int
    invoices_created: int
    errors: list[str] = []


class RetryRunResult(BaseModel):
    processed: int
    succeeded: int
    failed: int
    errors: list[str] = []


# ─── Generic Error ───────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
