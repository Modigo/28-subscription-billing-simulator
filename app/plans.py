from sqlalchemy.orm import Session
from app.models import Plan

def create_plan(db: Session, name: str, price_kobo: int, billing_interval: str = "monthly") -> Plan:
    if not name.strip():
        raise ValueError("Plan name is required.")
    if price_kobo < 0:
        raise ValueError("Plan price cannot be negative.")
    if billing_interval not in {"monthly", "yearly"}:
        raise ValueError("billing_interval must be monthly or yearly.")
    plan = Plan(name=name.strip(), price_kobo=price_kobo, billing_interval=billing_interval)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

def get_plans(db: Session, active_only: bool = True) -> list[Plan]:
    query = db.query(Plan)
    if active_only:
        query = query.filter(Plan.is_active.is_(True))
    return query.order_by(Plan.id).all()

def deactivate_plan(db: Session, plan_id: int) -> Plan:
    plan = db.get(Plan, plan_id)
    if not plan:
        raise ValueError("Plan not found.")
    plan.is_active = False
    db.commit()
    db.refresh(plan)
    return plan