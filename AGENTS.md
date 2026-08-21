# AGENTS.md — WorkforceOS Guidelines & Project Reference for AI Agents

> **WorkforceOS** is an enterprise-grade AI Workforce Management System built with a **FastAPI + Async SQLAlchemy** backend and a **React 19 + TypeScript + Vite** frontend, architected for high-concurrency multi-user production environments with Nginx load balancing and automated CI/CD.

---

## 🏗️ Technical Architecture & Stack

### Backend Stack
- **Framework**: FastAPI `0.115.6` with `uvicorn` (multi-worker ASGI setup)
- **Database**: PostgreSQL (driver: `asyncpg`) or SQLite fallback via SQLAlchemy `2.0.36` (Async ORM)
- **Migrations**: Alembic `1.14.0`
- **Validation**: Pydantic `2.10.3` (Pydantic v2 style models)
- **Authentication**: JWT (`python-jose`) with `bcrypt` password hashing (`passlib`)
- **Security**: `SecurityHeadersMiddleware` (CSP, HSTS, X-Frame-Options, X-Content-Type), `TrustedHostMiddleware`, strict CORS
- **Python Version**: Python 3.10+

### Frontend Stack
- **Framework**: React `19.2.7` with Vite `8.1.1`
- **Language**: TypeScript `6.0.2`
- **Routing**: React Router `7.18.1`
- **Visualizations**: Recharts `3.10.0`
- **Icons**: Lucide React `1.25.0`
- **HTTP Client**: Axios `1.18.1`
- **Notifications**: Custom animated Toast notification context (`ToastContext.tsx`)
- **Styling**: Modern Glassmorphism Vanilla CSS with HSL variables, skeleton shimmer, keyframe animations (`src/index.css`)
- **Linter**: Oxlint `1.71.0`

### Concurrency & Deployment Stack
- **Load Balancer / Reverse Proxy**: Nginx Alpine with `least_conn` load distribution, connection keepalive, rate limiting (`limit_req_zone`), and compression
- **Container Orchestration**: Multi-container `docker-compose.yml` supporting multi-replica scaling (`--scale backend=3`)
- **CI/CD Pipeline**: GitHub Actions (`.github/workflows/ci.yml` for automated test suites, bandit security analysis, frontend typecheck, and file integrity; `.github/workflows/cd.yml` for container builds and deployment)

---

## 📁 Directory & Component Structure

```
WorkforceOS/
├── AGENTS.md                     # Agent directives & repository guidelines
├── README.md                     # Public documentation & setup instructions
├── check_dependencies.py         # Static code analysis tool for broken imports & schema drift
├── docker-compose.yml            # Multi-user scalable Docker orchestration
├── .github/
│   └── workflows/
│       ├── ci.yml                # CI: Tests, lint, bandit security & file integrity
│       └── cd.yml                # CD: Docker image builds & deployment
├── scripts/
│   └── verify_nonempty.py        # Validates no repository files are empty/corrupted
├── nginx/
│   └── nginx.conf                # Nginx reverse proxy, load balancer & rate limiter
├── backend/                      # FastAPI Backend Root
│   ├── alembic.ini               # Alembic migration configuration
│   ├── Dockerfile                # Multi-worker non-root container image
│   ├── entrypoint.sh             # Auto-migration & Uvicorn startup script
│   ├── requirements.txt          # Python dependencies
│   ├── verify_attendance.py      # Attendance module integration test suite
│   ├── verify_employee.py        # Employee module integration test suite
│   ├── verify_insights.py        # Analytics & ML dataset test suite
│   ├── verify_leave.py           # Leave lifecycle & balance accrual test suite
│   ├── verify_payroll.py         # Payroll generation & payslip approval test suite
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint, security middlewares & routers
│   │   ├── api/
│   │   │   ├── dependencies/     # FastAPI auth guards (`auth.py`, role checks)
│   │   │   └── routes/           # API Endpoints (`auth`, `employees`, `departments`, `attendance`, `leave`, `payroll`, `insights`, `audit_logs`)
│   │   ├── core/                 # Database engine (`database.py`) & JWT security (`security.py`)
│   │   ├── models/               # SQLAlchemy ORM models (`base.py`, `user.py`, `employee.py`, `department.py`, `attendance.py`, `leave.py`, `payroll.py`, `audit_log.py`)
│   │   ├── repositories/         # Async data access layer (`employee_repository.py`, `payroll_repository.py`, etc.)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── services/             # Core business logic layer (`employee_service.py`, `payroll_service.py`, etc.)
│   └── migrations/               # Alembic database migration scripts
└── frontend/                     # React Frontend Root
    ├── package.json              # NPM dependencies & build scripts
    ├── Dockerfile                # Multi-stage production Nginx container
    ├── nginx.conf                # SPA router config with static caching
    ├── index.html                # Vite HTML entry point
    ├── vite.config.ts            # Vite dev server & API proxy config
    └── src/
        ├── App.tsx               # Main routing, ToastProvider & protected layout wrapper
        ├── index.css             # Design tokens, glassmorphism utilities & animations
        ├── api/                  # Axios instance (`client.ts`) & endpoint services
        ├── components/           # UI components (`Sidebar`, `TopBar`, `StatCard`, `Modal`, etc.)
        ├── context/              # React AuthContext, ToastContext & session management
        ├── pages/                # Views (`Dashboard`, `Employees`, `Departments`, `Attendance`, `Leave`, `Payroll`, `Insights`, `AuditLogs`, `Login`)
        └── types/                # TypeScript interfaces & domain types
```

---

## 🔑 Core Architectural Conventions

When inspecting or modifying code in this codebase, **always adhere to these principles**:

### 1. Primary Key Standard: UUID Everywhere
- All core entities (`User`, `Employee`, `Department`, `Attendance`, `LeaveRequest`, `LeaveBalance`, `PayrollPeriod`, `Payslip`, `AuditLog`) use **UUID primary keys**.
- Models inherit `UUIDPrimaryKeyMixin` from `app.models.base`.
- Model definitions declare IDs as `id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)`.
- Route parameters and schema attributes expecting entity IDs MUST use `uuid.UUID` or `UUID` strings. Never assume integer primary keys.

### 2. Soft Delete Pattern
- Key entities (`User`, `Employee`, `Department`) inherit `SoftDeleteMixin` (`is_deleted: bool = False`, `deleted_at: datetime | None = None`).
- Offboarding or deleting an entity performs a **logical soft delete** (setting `is_deleted = True`), NOT a SQL `DELETE`.
- All default repository query methods (`get_by_id`, `list`, etc.) MUST include `where(Entity.is_deleted == False)` unless `include_deleted=True` is explicitly passed.

### 3. Layered Separation of Concerns
1. **API Routes** (`app/api/routes/`): Validate inputs via Pydantic schemas, invoke Service layer, handle HTTP responses. Do not execute direct SQL or database transactions here.
2. **Services** (`app/services/`): Enforce business rules, check authorization constraints, handle audit logging, execute transactional units of work.
3. **Repositories** (`app/repositories/`): Perform isolated database operations using SQLAlchemy `AsyncSession`.
4. **Models** (`app/models/`): Declare database table structure and relationships.

### 4. Async Database Operations & Concurrency
- All database queries use **async SQLAlchemy 2.0 syntax**: `select(...)`, `await db.execute(...)`, `await db.flush()`, `await db.commit()`.
- Use `AsyncSession` injected via FastAPI dependency `get_db` from `app.core.database`.
- Database engine uses connection pooling (`pool_size=20, max_overflow=10`).
- Never call synchronous engine methods or blocking calls in async route endpoints.

### 5. Audit Logging Rule
- Any state-altering business operation (Onboard, Update, Offboard Employee, Leave Approval/Rejection, Payroll Approval, Department Creation) MUST record an `AuditLog` entry detailing:
  - `user_id`: Operator user ID
  - `action`: Specific action code (e.g. `ONBOARD_EMPLOYEE`, `APPROVE_PAYROLL_PERIOD`)
  - `target_type`: Affected table name (e.g. `employees`, `payroll_periods`)
  - `target_id`: Affected entity UUID
  - `changes`: JSON diff of old/new values

### 6. Security Standards
- **No Wildcard CORS in Production**: Origins configured via `ALLOWED_ORIGINS` environment variable.
- **Security Headers**: Enforced via `SecurityHeadersMiddleware` (CSP, HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY).
- **Anti-Host-Injection**: Handled by `TrustedHostMiddleware`.
- **Rate Limiting**: Configured at Nginx reverse proxy level for general APIs (`30r/s`) and Auth routes (`5r/s`).

---

## 🛠️ Verification & Quality Assurance Commands

AI agents making changes to this codebase MUST verify their work using the following commands before finalizing tasks:

### 1. Static Dependency & Schema Audit
Run the custom static dependency checker from the project root to detect broken imports, non-existent model references, or UUID/soft-delete mismatches:
```bash
python check_dependencies.py
```

### 2. File Integrity & Non-Empty Check
Run the repository scanner to ensure no empty or corrupted files exist:
```bash
python scripts/verify_nonempty.py
```

### 3. Backend Verification Suites
Run module-specific verification scripts in `backend/` to validate database interactions and business logic:
```bash
cd backend

# Verify Employee lifecycle & audit logging
python verify_employee.py

# Verify Attendance check-in/out & late calculation
python verify_attendance.py

# Verify Leave applications, approvals & balance accruals
python verify_leave.py

# Verify Payroll generation, deduction calculations & payslip approval
python verify_payroll.py

# Verify Insights & ML turnover risk datasets
python verify_insights.py
```

### 4. Frontend Typechecking & Linting
Run TypeScript compilation and Oxlint in `frontend/`:
```bash
cd frontend

# Verify TypeScript types and production build
npm run build

# Run fast code linting
npm run lint
```

---

## 🎨 UI Design System Rules (Frontend)

- **Style Framework**: Pure Vanilla CSS with HSL design tokens declared in `frontend/src/index.css`.
- **Aesthetic**: Modern Glassmorphism. Dark background (`--bg-dark`), translucent card backdrops (`backdrop-filter: blur()`), glowing border gradients, and HSL accents (`--primary`, `--accent-cyan`, `--accent-purple`, `--accent-emerald`, `--accent-amber`, `--accent-rose`).
- **Interactive Feedback**: All interactive elements (buttons, inputs, cards) require smooth CSS transitions (`transition: all 0.2s ease`) and dynamic hover states.
- **Feedback & Alerts**: Use custom `useToast()` notifications (`ToastContext.tsx`) instead of native browser `alert()` or `confirm()`.
- **Icons**: Use `lucide-react` icons exclusively.
- **Charts**: Use `recharts` responsive containers for data visualization.

---

## 🚫 Agent Safeguards & Rules of Conduct

1. **Do Not Break Soft Delete**: Never replace soft delete calls with hard `DELETE FROM table` queries unless explicitly instructed.
2. **Do Not Mix Sync and Async**: Never inject synchronous database calls into FastAPI async handlers.
3. **Preserve API Contracts**: When modifying schemas or routes, ensure frontend API types in `frontend/src/types/` remain aligned with backend Pydantic schemas in `backend/app/schemas/`.
4. **Register Routes**: New route files created under `backend/app/api/routes/` MUST be mounted in `backend/app/main.py` using `app.include_router(router, prefix="/api")`.
5. **Always Verify**: Run `python scripts/verify_nonempty.py`, `python check_dependencies.py`, and `npm run build` to ensure no breaking changes were introduced.
