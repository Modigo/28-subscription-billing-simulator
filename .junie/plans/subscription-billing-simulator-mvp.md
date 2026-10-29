---
sessionId: session-261029-123444-2m88
---

# Requirements

## Requirements

### Overview & Goals
Build a complete, functional MVP for a **Subscription Billing Simulator** that demonstrates recurring subscription billing without real payment processing. The application will be suitable for a team project, live demonstration, and deployment.

### Scope

**In Scope:**
- Plan management (CRUD + retirement)
- Customer management (CRUD)
- Subscription management (create, pause, resume, cancel, plan changes)
- Invoice generation (idempotent, decimal-safe)
- Simulated payments (success/failure)
- Failed-payment retry engine (configurable schedule)
- Recurring billing scheduler (manual trigger)
- Dashboard with metrics and reporting
- React frontend connected to real API
- Comprehensive tests
- Docker Compose for local development
- Deployment-ready configuration

**Out of Scope:**
- Real payment provider integration (Stripe, Paystack, etc.)
- Authentication/authorization (MVP demo mode only)
- Background workers (manual triggers for MVP)
- Complex proration for immediate plan changes
- Multi-tenant support

### User Stories
1. As a demo user, I want to create subscription plans so I can define billing options.
2. As a demo user, I want to register customers so I can subscribe them to plans.
3. As a demo user, I want to subscribe customers to plans so I can simulate billing cycles.
4. As a demo user, I want to simulate payment success and failure so I can demonstrate retry logic.
5. As a demo user, I want to run the billing scheduler so I can see recurring invoices generated.
6. As a demo user, I want to view dashboard metrics so I can see billing activity at a glance.

### Functional Requirements
- All timestamps stored in UTC
- Decimal-safe money calculations (no binary floating-point)
- Idempotent invoice generation (no duplicates for same billing period)
- Configurable retry schedule (3, 7, 14 days default)
- Injectable clock for testable retry scheduling
- Manual trigger buttons for billing and retry (no auto-execution on page load)
- Simulated payments clearly labeled in the UI
- Database constraints for important invariants
- Proper transaction boundaries for multi-record operations

### Non-Functional Requirements
- PostgreSQL only (no SQLite fallback)
- CORS configured for frontend origin
- No hardcoded secrets
- Environment-based configuration
- Structured logging for billing operations
- Clear separation between API routes and business logic
- Consistent error responses (no raw stack traces)
- Responsive UI (desktop and mobile)

# Technical Design

## Technical Design

### Current Implementation
**Empty repository** — Only `README.md` and IDE config files exist. No backend, frontend, database, or test code has been implemented. The project requires building the entire stack from scratch.

### Architecture
```
graph LR
    A[React Frontend] --> B[FastAPI Backend]
    B --> C[PostgreSQL]
    B --> D[Services Layer]
    D --> C
```

### Backend Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Environment-based configuration
│   │   └── database.py         # SQLAlchemy engine/session setup
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── customer.py
│   │   ├── plan.py
│   │   ├── subscription.py
│   │   ├── invoice.py
│   │   ├── payment_attempt.py
│   │   ├── plan_change.py
│   │   └── billing_event.py
│   ├── schemas/                # Pydantic request/response schemas
│   ├── api/
│   │   └── routes/             # REST endpoints under /api/v1
│   │       ├── plans.py
│   │       ├── customers.py
│   │       ├── subscriptions.py
│   │       ├── invoices.py
│   │       ├── billing.py
│   │       └── dashboard.py
│   ├── services/               # Business logic
│   │   ├── plan_service.py
│   │   ├── customer_service.py
│   │   ├── subscription_service.py
│   │   ├── invoice_service.py
│   │   ├── payment_service.py
│   │   ├── retry_service.py
│   │   └── billing_service.py
│   └── utils/
│       └── clock.py            # Injectable clock for testing
├── alembic/                    # Database migrations
├── tests/                      # pytest tests
├── requirements.txt
├── alembic.ini
└── .env.example
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/             # Shared UI components
│   │   ├── StatusBadge.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── Layout.tsx
│   │   └── Navigation.tsx
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Plans.tsx
│   │   ├── Customers.tsx
│   │   ├── Subscriptions.tsx
│   │   ├── Invoices.tsx
│   │   └── BillingOperations.tsx
│   ├── services/               # API client layer
│   │   └── api.ts
│   ├── types/                  # TypeScript types matching API schemas
│   ├── hooks/                  # Custom React hooks
│   └── utils/                  # Formatting utilities
├── package.json
└── .env.example
```

### Database Models

**Customer**: id, name, email (unique), created_at, updated_at

**Plan**: id, name, description, price (NUMERIC), currency (default NGN), billing_interval (monthly/yearly), trial_days (default 0), status (active/retired), created_at, updated_at

**Subscription**: id, customer_id (FK), plan_id (FK), status (trialing/active/past_due/suspended/canceled/paused), current_period_start, current_period_end, trial_end (nullable), canceled_at (nullable), created_at, updated_at

**Invoice**: id, subscription_id (FK), invoice_number (unique), amount (NUMERIC), currency, status (pending/paid/failed/void), billing_period_start, billing_period_end, issued_at, due_at, paid_at (nullable), attempt_count, next_retry_at (nullable), created_at, updated_at

**PaymentAttempt**: id, invoice_id (FK), attempt_number, outcome (success/failure), failure_reason (nullable), attempted_at

**PlanChangeHistory**: id, subscription_id (FK), old_plan_id, new_plan_id, effective_at, change_type (immediate/next_cycle), created_at

**BillingEvent**: id, event_type, subscription_id (FK), invoice_id (FK, nullable), details (JSON), created_at

### Key Decisions

1. **PostgreSQL only** — No SQLite fallback. All money fields use `NUMERIC` type.
2. **Decimal arithmetic** — All money calculations use Python `decimal.Decimal`, never binary floating-point.
3. **Injectable clock** — `utils/clock.py` provides a configurable clock that tests can override to simulate time passage for retry scheduling.
4. **Idempotent invoices** — Unique constraint on `(subscription_id, billing_period_start)` prevents duplicate invoices.
5. **Manual triggers** — Billing scheduler and retry processor are triggered via POST endpoints, not automatically on page load.
6. **Service layer separation** — Business logic lives in `services/`, not in API routes. Routes only handle HTTP concerns.
7. **Changes at next billing cycle** — Plan changes take effect at the next billing cycle by default (simpler than proration for MVP).
8. **Demo mode** — No authentication required; operational endpoints are publicly accessible for demo purposes.

### API Endpoints

| Resource | Endpoints |
|---|---|
| Health | `GET /health` |
| Plans | `GET, POST /api/v1/plans` |
| Individual plan | `GET, PATCH /api/v1/plans/{id}` |
| Retire plan | `POST /api/v1/plans/{id}/retire` |
| Customers | `GET, POST /api/v1/customers` |
| Customer details | `GET /api/v1/customers/{id}` |
| Subscriptions | `GET, POST /api/v1/subscriptions` |
| Subscription details | `GET /api/v1/subscriptions/{id}` |
| Subscription actions | `POST /api/v1/subscriptions/{id}/pause`, `/resume`, `/cancel` |
| Plan changes | `POST /api/v1/subscriptions/{id}/change-plan` |
| Invoices | `GET /api/v1/invoices` |
| Invoice details | `GET /api/v1/invoices/{id}` |
| Payment simulation | `POST /api/v1/invoices/{id}/simulate-payment` |
| Payment history | `GET /api/v1/invoices/{id}/attempts` |
| Billing scheduler | `POST /api/v1/billing/run` |
| Retry processor | `POST /api/v1/retries/run` |
| Dashboard metrics | `GET /api/v1/dashboard/summary` |
| Billing history | `GET /api/v1/events` |

### Risks
- **Decimal precision**: Ensure all money calculations use `Decimal` consistently, including in Pydantic schemas and JSON serialization.
- **Timezone handling**: All timestamps must be UTC-aware; naive datetime comparisons can cause bugs.
- **Idempotency**: Invoice generation must be truly idempotent even under concurrent requests.
- **Test isolation**: Tests must use a dedicated test database, not the production database.

# Testing

## Testing

### Backend Tests (pytest)

**Test database**: Dedicated PostgreSQL test database or isolated schema.

**Core test scenarios:**
1. Create plan successfully
2. Reject invalid plan prices (negative, zero)
3. Reject duplicate customer emails
4. Create subscription with active plan
5. Generate initial invoice on subscription creation (no trial)
6. Invoice amount matches plan price
7. Prevent duplicate invoices for same billing period
8. Simulate successful payment → invoice marked paid
9. Simulate failed payment → invoice marked failed, retry scheduled
10. Record payment attempts correctly
11. Reject invalid subscription state transitions (e.g., cancel → resume)
12. Process eligible retry successfully
13. Schedule another retry after failed retry
14. Exhaust retries → subscription becomes past_due/suspended
15. Skip retries not yet due
16. Billing scheduler generates no duplicate invoices
17. Plan change applied at next billing cycle
18. Dashboard metrics calculated correctly
19. Handle missing records (404) and invalid requests (422)
20. Concurrent processing safety (where practical)

**End-to-end scenario:**
1. Create customer → Create monthly plan → Subscribe customer → Generate invoice → Simulate failed payment → Confirm retry scheduled → Advance clock → Run retry processor → Simulate success → Confirm invoice paid, dashboard updated

**Failure scenario:**
All retries exhausted → subscription becomes past_due or suspended

### Frontend Tests

- Key form rendering and validation
- API error handling (display error messages)
- Status badge rendering
- Currency formatting
- End-to-end flow: create customer → subscribe → invoice → payment → retry

### Validation Approach
- Use pytest fixtures for test data isolation
- Use injectable clock to simulate time passage
- Verify database state after each operation
- Test transaction rollback on failures
- Verify idempotency by running operations twice

# Delivery Steps

### ✓ Step 1: Set up project foundation and database
Create the complete project structure, configure backend dependencies, set up PostgreSQL connection, and implement all database models with Alembic migrations.

- Create backend/ and frontend/ directory structures
- Configure backend: requirements.txt (FastAPI, SQLAlchemy, Pydantic, pytest, alembic, psycopg2), .env.example, alembic.ini
- Implement `app/core/config.py` with environment-based configuration
- Implement `app/core/database.py` with SQLAlchemy engine and session management
- Create all SQLAlchemy models: Customer, Plan, Subscription, Invoice, PaymentAttempt, PlanChangeHistory, BillingEvent
- Create Pydantic schemas for all entities (request and response)
- Set up Alembic and generate initial migration
- Create docker-compose.yml with PostgreSQL service
- Create .gitignore

### ✓ Step 2: Implement business logic services
Build all service-layer modules that contain the core billing business logic.

- `plan_service.py`: CRUD for plans, retirement logic, validation
- `customer_service.py`: CRUD for customers, email validation, duplicate prevention
- `subscription_service.py`: Create subscriptions, pause/resume/cancel, state machine for valid transitions
- `invoice_service.py`: Generate invoices with idempotency, decimal-safe calculations, unique invoice numbers
- `payment_service.py`: Simulate success/failure, record payment attempts, update invoice status
- `retry_service.py`: Process failed invoices, configurable retry schedule (3/7/14 days), injectable clock for testing
- `billing_service.py`: Recurring billing scheduler, period advancement, subscription status checks
- `utils/clock.py`: Injectable clock abstraction for testable time simulation
- Dashboard/reporting service: Aggregate metrics from database

### ✓ Step 3: Implement API routes and error handling
Create all REST endpoints under /api/v1, wire them to services, and configure error handling.

- `app/main.py`: FastAPI app with CORS, middleware, and lifespan events
- Health endpoint: `GET /health`
- Plans endpoints: CRUD + retire
- Customers endpoints: CRUD
- Subscriptions endpoints: CRUD + actions (pause, resume, cancel, change-plan)
- Invoices endpoints: list, detail, simulate-payment, payment attempts
- Billing operations: run billing scheduler, run retry processor
- Dashboard summary and billing events
- Global exception handler for consistent error responses
- Proper HTTP status codes (201, 204, 400, 404, 409, 422)
- Pagination for collection endpoints

### ✓ Step 4: Build React frontend
Create the React + Vite + TypeScript + Tailwind CSS frontend with all pages connected to the real API.

- Set up frontend: Vite + React + TypeScript + Tailwind CSS, package.json, .env.example
- API service layer (`src/services/api.ts`) with TypeScript types matching backend schemas
- Shared components: StatusBadge, ConfirmDialog, Layout, Navigation, Date/Currency formatters
- Dashboard page: metrics cards, recent invoices, billing activity, quick action buttons
- Plans page: list, create form, edit form, retire action
- Customers page: list, create form, details with subscriptions and invoices
- Subscriptions page: list, create form, status indicators, pause/resume/cancel/change-plan actions
- Invoices page: list, detail view, payment history, simulate payment actions
- Billing Operations page: run scheduler and retry processor buttons with results display
- Loading, error, and empty states throughout
- Responsive layout for desktop and mobile

### ✓ Step 5: Write tests and seed data
Implement comprehensive backend tests, frontend tests, and seed data for demonstrations.

- Backend tests (pytest): 20+ test cases covering all core scenarios
- Test fixtures for database isolation and injectable clock
- End-to-end test: create customer → subscribe → invoice → failed payment → retry → success
- Failure scenario test: all retries exhausted → subscription suspended
- Idempotency tests: duplicate invoice prevention
- Frontend tests: form validation, API error handling, status rendering
- Seed data command: idempotent script to create demo customers, plans, subscriptions, invoices, and payment history
- Test configuration: dedicated test database, pytest fixtures

### ✓ Step 6: Finalize documentation and deployment
Complete the README, verify the full stack works end-to-end, and prepare for deployment.

- Comprehensive README with: project overview, tech stack, architecture, directory structure, database entities, API docs, environment variables, local setup instructions, migration instructions, seed data instructions, test instructions, deployment instructions, demo script, known limitations, future improvements
- Verify docker-compose starts PostgreSQL and the application
- Verify migrations run on clean database
- Verify seed data loads correctly
- Verify all API endpoints work
- Verify frontend connects to backend and displays real data
- Verify tests pass
- Production build configuration for frontend
- Deployment configuration documentation
- Final integration testing of the complete demo flow

### ✓ Step 7: Deploy for team presentation
Build production frontend, configure CORS for deployed URLs, and deploy backend + frontend to free-tier hosting services so the team can access the app online.

- Created `backend/render.yaml` for Render deployment configuration
- Created `frontend/vercel.json` for Vercel deployment configuration
- Created `DEPLOYMENT.md` with step-by-step deployment guide
- Fixed TypeScript build errors (unused imports, missing type definitions)
- Created `frontend/src/vite-env.d.ts` for Vite environment types
- Updated `README.md` with deployment section
- Frontend production build verified successfully