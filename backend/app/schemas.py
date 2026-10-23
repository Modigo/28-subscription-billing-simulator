from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# CUSTOMER SCHEMAS

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


# PLAN SCHEMAS

class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_kobo: int = Field(ge=0)
    billing_interval: str = "monthly"


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_kobo: int
    billing_interval: str
    is_active: bool
    created_at: datetime


# SUBSCRIPTION SCHEMAS

class SubscriptionCreate(BaseModel):
    customer_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    plan_id: int
    status: str
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    next_billing_date: datetime
    canceled_at: datetime | None


# INVOICE SCHEMA

class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    subscription_id: int
    billing_period_start: datetime
    billing_period_end: datetime
    issue_date: datetime
    due_date: datetime
    amount_kobo: int
    status: str
    created_at: datetime