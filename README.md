# Subscription Billing Simulator

A complete MVP for recurring subscription billing without real payment processing. Built with **FastAPI**, **PostgreSQL**, **React**, and **TypeScript**.

## Overview

This application simulates a subscription billing system where you can:
- Create and manage subscription plans
- Register customers and subscribe them to plans
- Generate invoices with decimal-safe calculations
- Simulate payment success and failure
- Retry failed payments on a configurable schedule (3, 7, 14 days)
- Run recurring billing cycles manually
- View dashboard metrics and billing history

**All payments are simulated** — no real money is charged.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Testing | pytest |
| Containerization | Docker Compose |

## Architecture

```
React Frontend → FastAPI Backend → PostgreSQL
                     ↓
              Services Layer (business logic)
```

## Project Structure

```
subscription-billing-simulator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── core/                # Config, database setup
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── api/routes/          # REST endpoints (/api/v1)
│   │   ├── services/            # Business logic
│   │   ├── utils/clock.py       # Injectable clock for testing
│   │   └── seed_data.py         # Demo data seeder
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # Shared UI components
│   │   ├── pages/               # Page components
│   │   ├── services/api.ts      # API client
│   │   ├── types/               # TypeScript types
│   │   └── utils/               # Formatting utilities
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
└── .gitignore
```

## Database Entities

- **Customer** — id, name, email (unique), timestamps
- **Plan** — id, name, price (NUMERIC), currency, billing_interval, trial_days, status
- **Subscription** — id, customer_id, plan_id, status, billing period, trial/cancel dates
- **Invoice** — id, subscription_id, invoice_number (unique), amount (NUMERIC), status, billing period, plan snapshot
- **PaymentAttempt** — id, invoice_id, attempt_number, outcome, failure_reason
- **PlanChangeHistory** — id, subscription_id, old/new plan, effective_at, change_type
- **BillingEvent** — id, event_type, subscription_id, invoice_id, details (JSON)

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or use Docker Compose)

### Option 1: Docker Compose (Recommended)

```bash
docker compose up --build
```

This starts PostgreSQL, the backend (port 8000), and the frontend (port 5173).

### Option 2: Manual Setup

#### 1. Start PostgreSQL

```bash
docker run --name billing-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=billing_db -p 5432:5432 -d postgres:16-alpine
```

#### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database URL

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.seed_data

# Start server
uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173 in your browser.

## API Endpoints

| Resource | Endpoints |
|---|---|
| Health | `GET /health` |
| Plans | `GET, POST /api/v1/plans` |
| Plan detail | `GET, PATCH /api/v1/plans/{id}` |
| Retire plan | `POST /api/v1/plans/{id}/retire` |
| Customers | `GET, POST /api/v1/customers` |
| Customer detail | `GET /api/v1/customers/{id}` |
| Subscriptions | `GET, POST /api/v1/subscriptions` |
| Subscription detail | `GET /api/v1/subscriptions/{id}` |
| Pause/Resume/Cancel | `POST /api/v1/subscriptions/{id}/pause`, `/resume`, `/cancel` |
| Change plan | `POST /api/v1/subscriptions/{id}/change-plan` |
| Invoices | `GET /api/v1/invoices` |
| Invoice detail | `GET /api/v1/invoices/{id}` |
| Simulate payment | `POST /api/v1/invoices/{id}/simulate-payment` |
| Payment history | `GET /api/v1/invoices/{id}/attempts` |
| Billing scheduler | `POST /api/v1/billing/run` |
| Retry processor | `POST /api/v1/retries/run` |
| Dashboard | `GET /api/v1/dashboard/summary` |
| Events | `GET /api/v1/events` |

Swagger UI is available at http://localhost:8000/docs.

## Environment Variables

### Backend

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/billing_db` | Database connection |
| `APP_ENV` | `development` | Environment name |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `DEMO_MODE` | `true` | Enable demo mode (no auth) |
| `RETRY_SCHEDULE` | `3,7,14` | Days between retry attempts |

### Frontend

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API URL |

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database for isolation.

## Demo Script

1. **Open the dashboard** — View metrics and recent activity
2. **Create a plan** — Go to Plans → New Plan (e.g., "Pro Plan", ₦15,000/month)
3. **Create a customer** — Go to Customers → New Customer
4. **Subscribe** — Go to Subscriptions → New Subscription, select customer and plan
5. **View invoice** — Go to Invoices, click View on the generated invoice
6. **Simulate failure** — In the invoice detail, click "Simulate Failure"
7. **Check retry** — Note the next retry date (3 days from now)
8. **Run retry processor** — Go to Billing Ops → Run Retry Processor
9. **Simulate success** — In the invoice detail, click "Simulate Success"
10. **Check dashboard** — Revenue and metrics are updated

## Known Limitations

- No authentication — demo mode only
- No background workers — billing and retry are manual triggers
- No proration — plan changes take effect at next billing cycle by default
- SQLite used for tests — production requires PostgreSQL
- No email notifications

## Deployment

For step-by-step deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deploy Summary

1. **Backend** → Deploy to [Render](https://render.com) (free tier)
2. **Frontend** → Deploy to [Vercel](https://vercel.com) (free tier)
3. **Database** → Already on [Supabase](https://supabase.com) PostgreSQL

After deployment, your team can access the app online 24/7, even when your computer is off.

> **Note:** Render's free tier sleeps after 15 minutes of inactivity. Visit the backend URL a few minutes before your presentation to wake it up.

## Future Improvements

- Authentication and authorization
- Background worker for automatic billing cycles
- Prorated plan changes
- Email notifications for invoice events
- Real payment provider integration (Stripe, Paystack)
- Multi-currency support with exchange rates
- Export billing reports (CSV/PDF)
- Webhook support for external integrations
