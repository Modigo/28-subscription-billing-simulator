"""Plan management service."""

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.schemas import PlanCreate, PlanUpdate


class PlanService:
    """Business logic for plan CRUD and retirement."""

    @staticmethod
    def list_plans(db: Session, status: str | None = None) -> list[Plan]:
        """List plans, optionally filtered by status."""
        query = db.query(Plan)
        if status:
            query = query.filter(Plan.status == status)
        return query.order_by(Plan.created_at.desc()).all()

    @staticmethod
    def get_plan(db: Session, plan_id: int) -> Plan | None:
        """Get a plan by ID."""
        return db.query(Plan).filter(Plan.id == plan_id).first()

    @staticmethod
    def create_plan(db: Session, data: PlanCreate) -> Plan:
        """Create a new plan."""
        plan = Plan(
            name=data.name,
            description=data.description,
            price=data.price,
            currency=data.currency,
            billing_interval=data.billing_interval,
            trial_days=data.trial_days,
            status="active",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def update_plan(db: Session, plan_id: int, data: PlanUpdate) -> Plan | None:
        """Update an existing plan."""
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if plan is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(plan, key, value)

        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def retire_plan(db: Session, plan_id: int) -> Plan | None:
        """Retire a plan so it cannot be used for new subscriptions."""
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if plan is None:
            return None
        plan.status = "retired"
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def get_active_plans(db: Session) -> list[Plan]:
        """Get all active plans for subscription creation."""
        return db.query(Plan).filter(
            Plan.status == "active"
        ).order_by(Plan.name).all()
