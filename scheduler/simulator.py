
from datetime import date
from calendar import monthrange

# Sample subscriptions
subscriptions = [
    {
        "customer": "Helen",
        "price": 5000,
        "status": "active",
        "next_billing_date": date(2026, 10, 20),
        "payment_success": True,
        "retries": 0
    },
    {
        "customer": "John",
        "price": 3000,
        "status": "active",
        "next_billing_date": date(2026, 10, 15),
        "payment_success": False,
        "retries": 0
    },
    {
        "customer": "Mary",
        "price": 7000,
        "status": "cancelled",
        "next_billing_date": date(2026, 10, 1),
        "payment_success": True,
        "retries": 0
    }
]


# Move the billing date forward by one month
def next_month(billing_date):
    year = billing_date.year
    month = billing_date.month + 1

    if month > 12:
        month = 1
        year += 1

    day = min(
        billing_date.day,
        monthrange(year, month)[1]
    )

    return date(year, month, day)


# Find subscriptions that are due
def find_due_subscriptions(subscriptions, today):
    due = []

    for subscription in subscriptions:
        if (
            subscription["status"] == "active"
            and subscription["next_billing_date"] <= today
        ):
            due.append(subscription)

    return due


# Simulate billing
def run_billing(subscriptions, today):
    due = find_due_subscriptions(subscriptions, today)

    if not due:
        print("No subscriptions are due for billing.")
        return

    for subscription in due:
        print("\nCustomer:", subscription["customer"])
        print("Invoice amount: ₦", subscription["price"])

        if subscription["payment_success"]:
            print("Payment successful!")

            subscription["next_billing_date"] = next_month(
                subscription["next_billing_date"]
            )
            subscription["retries"] = 0

            print("Invoice status: PAID")
            print(
                "Next billing date:",
                subscription["next_billing_date"]
            )

        else:
            subscription["retries"] += 1

            print("Payment failed!")
            print("Invoice status: FAILED")
            print("Retry attempt:", subscription["retries"])

            if subscription["retries"] >= 3:
                print("Maximum retries reached.")
            else:
                print("Payment can be retried later.")


# Run the simulator
today = date(2026, 10, 20)
run_billing(subscriptions, today)
