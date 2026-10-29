"""Customer management service."""

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas import CustomerCreate


class CustomerService:
    """Business logic for customer CRUD."""

    @staticmethod
    def list_customers(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[Customer]:
        """List customers with pagination."""
        return (
            db.query(Customer)
            .order_by(Customer.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Customer | None:
        """Get a customer by ID."""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def get_customer_by_email(db: Session, email: str) -> Customer | None:
        """Get a customer by email."""
        return (
            db.query(Customer)
            .filter(Customer.email == email.lower())
            .first()
        )

    @staticmethod
    def create_customer(db: Session, data: CustomerCreate) -> Customer:
        """Create a new customer."""
        customer = Customer(
            name=data.name,
            email=data.email.lower(),
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def count_customers(db: Session) -> int:
        """Count total customers."""
        return db.query(Customer).count()
