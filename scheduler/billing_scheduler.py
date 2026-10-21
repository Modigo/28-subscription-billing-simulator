from datetime import date

subscriptions = [
    {
        "customer": "Helen",
        "price": 5000,
        "status": "active",
        "next_billing_date": date(2026, 10, 20)
    },
    {
        "customer": "John",
        "price": 3000,
        "status": "active",
        "next_billing_date": date(2026, 10, 15)
    },
    {
        "customer": "Mary",
        "price": 7000,
        "status": "cancelled",
        "next_billing_date": date(2026, 10, 1)
    }
]


def find_due_subscriptions(subscriptions, today):
    due_subscriptions = []

    for subscription in subscriptions:
        if (
            subscription["status"] == "active"
            and subscription["next_billing_date"] <= today
        ):
            due_subscriptions.append(subscription)

    return due_subscriptions


def run_scheduler(subscriptions, today):
    due = find_due_subscriptions(subscriptions, today)

    print("BILLING SCHEDULER")
    print("Today's date:", today)

    if not due:
        print("No subscriptions are due.")
        return

    for subscription in due:
        print("\nCustomer:", subscription["customer"])
        print("Amount: ₦", subscription["price"])
        print("Billing date:", subscription["next_billing_date"])
        print("Status: DUE")


if __name__ == "__main__":
    run_scheduler(subscriptions, date.today())
