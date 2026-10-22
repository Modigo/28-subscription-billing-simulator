import sqlite3

DATABASE_NAME = "billing.db"


def get_connection():
    """Open a connection to the billing database."""
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the invoices table if it does not exist."""

    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices(
                invoice_id TEXT PRIMARY KEY,
                subscription_id TEXT NOT NULL,
                amount_kobo INTEGER NOT NULL CHECK(amount_kobo >= 0),
                billing_period_start TEXT NOT NULL,
                billing_period_end TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
            
                UNIQUE(
                    subscription_id,
                    billing_period_start,
                    billing_period_end
                ),
                CHECK(billing_period_end > billing_period_start)
            )
        """)

        connection.commit()
    finally:
        connection.close
