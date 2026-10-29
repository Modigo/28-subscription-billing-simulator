version = "2023_03_08"

"""Initial migration

Revision ID: initial
Revises: 
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Customers
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Plans
    billing_interval_enum = sa.Enum("monthly", "yearly", name="billing_interval_enum")
    plan_status_enum = sa.Enum("active", "retired", name="plan_status_enum")
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="NGN"),
        sa.Column("billing_interval", billing_interval_enum, nullable=False),
        sa.Column("trial_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", plan_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Subscriptions
    subscription_status_enum = sa.Enum(
        "trialing", "active", "past_due", "suspended", "canceled", "paused",
        name="subscription_status_enum"
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", subscription_status_enum, nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Invoices
    invoice_status_enum = sa.Enum("pending", "paid", "failed", "void", name="invoice_status_enum")
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer, sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("invoice_number", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", invoice_status_enum, nullable=False, server_default="pending"),
        sa.Column("billing_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("billing_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("plan_name", sa.String(255), nullable=True),
        sa.Column("plan_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("subscription_id", "billing_period_start", name="uq_subscription_period"),
    )

    # Payment attempts
    payment_outcome_enum = sa.Enum("success", "failure", name="payment_outcome_enum")
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("outcome", payment_outcome_enum, nullable=False),
        sa.Column("failure_reason", sa.Text, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Plan change history
    plan_change_type_enum = sa.Enum("immediate", "next_cycle", name="plan_change_type_enum")
    op.create_table(
        "plan_change_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer, sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("old_plan_id", sa.Integer, nullable=False),
        sa.Column("new_plan_id", sa.Integer, nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("change_type", plan_change_type_enum, nullable=False, server_default="next_cycle"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Billing events
    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("subscription_id", sa.Integer, sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("billing_events")
    op.drop_table("plan_change_history")
    op.drop_table("payment_attempts")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("customers")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS billing_interval_enum")
    op.execute("DROP TYPE IF EXISTS plan_status_enum")
    op.execute("DROP TYPE IF EXISTS subscription_status_enum")
    op.execute("DROP TYPE IF EXISTS invoice_status_enum")
    op.execute("DROP TYPE IF EXISTS payment_outcome_enum")
    op.execute("DROP TYPE IF EXISTS plan_change_type_enum")
