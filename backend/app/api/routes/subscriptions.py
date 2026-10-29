"""Subscriptions API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    SubscriptionChangePlan,
    SubscriptionCreate,
    SubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
def list_subscriptions(
    customer_id: int | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    subs = SubscriptionService.list_subscriptions(
        db, customer_id=customer_id, status=status, skip=skip, limit=limit
    )
    return subs


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(data: SubscriptionCreate, db: Session = Depends(get_db)):
    try:
        sub = SubscriptionService.create_subscription(
            db, customer_id=data.customer_id, plan_id=data.plan_id
        )
        return sub
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    sub = SubscriptionService.get_subscription(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.post("/subscriptions/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(subscription_id: int, db: Session = Depends(get_db)):
    try:
        sub = SubscriptionService.pause_subscription(db, subscription_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/subscriptions/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(subscription_id: int, db: Session = Depends(get_db)):
    try:
        sub = SubscriptionService.resume_subscription(db, subscription_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)):
    try:
        sub = SubscriptionService.cancel_subscription(db, subscription_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post(
    "/subscriptions/{subscription_id}/change-plan",
    response_model=SubscriptionResponse,
)
def change_plan(
    subscription_id: int,
    data: SubscriptionChangePlan,
    db: Session = Depends(get_db),
):
    try:
        sub = SubscriptionService.change_plan(
            db, subscription_id, data.plan_id, data.change_type
        )
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
