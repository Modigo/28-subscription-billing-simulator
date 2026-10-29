"""Customers API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import CustomerCreate, CustomerDetailResponse, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter()


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    customers = CustomerService.list_customers(db, skip=skip, limit=limit)
    return customers


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    # Check for duplicate email
    existing = CustomerService.get_customer_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Customer with email {data.email} already exists"
        )
    customer = CustomerService.create_customer(db, data)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = CustomerService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
