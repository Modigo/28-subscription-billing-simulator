"""Plans API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import PlanCreate, PlanResponse, PlanUpdate
from app.services.plan_service import PlanService

router = APIRouter()


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    plans = PlanService.list_plans(db, status=status)
    return plans


@router.post("/plans", response_model=PlanResponse, status_code=201)
def create_plan(data: PlanCreate, db: Session = Depends(get_db)):
    plan = PlanService.create_plan(db, data)
    return plan


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = PlanService.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db)):
    plan = PlanService.update_plan(db, plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/plans/{plan_id}/retire", response_model=PlanResponse)
def retire_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = PlanService.retire_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
