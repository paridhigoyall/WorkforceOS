# WorkforceOS — AI Enterprise Workforce Management System

WorkforceOS is a full-stack, enterprise-grade AI Workforce Management platform built with FastAPI, PostgreSQL/SQLAlchemy, and React with TypeScript.

---

## 🌟 Key Features

### Backend (FastAPI + Async SQLAlchemy)
- **JWT Authentication & RBAC**: Roles (`admin`, `hr`, `staff`) with bcrypt hashing and OAuth2 compliance.
- **Employee Lifecycle**: Onboarding, profile updates, base salary tracking, and soft-delete offboarding.
- **Department Management**: Business unit tracking, department codes, and headcount metrics.
- **Attendance Engine**: Daily check-in/out, automatic late check-in detection, and overtime calculations.
- **Leave Lifecycle**: Annual, sick, casual, maternity, and unpaid leave application, balance tracking, and manager approval workflows.
- **AI Analytics & Predictions**: Department payroll aggregations, attendance rates, leave utilization, and Machine Learning turnover risk dataset endpoint.

### Frontend (React + TypeScript + Vite)
- **Modern Glassmorphism UI**: Dark mode, vibrant HSL color tokens, micro-animations, and fluid layout.
- **Interactive Dashboards**: Live KPI cards, quick punch-in/out, pending approvals, and system status indicators.
- **Data Visualizations**: Recharts integration for monthly department payroll and leave days distribution.
- **Predictive Risk Dataset**: Interactive table displaying AI turnover risk classifications (Low / Medium / High).

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (or SQLite/Asyncpg fallback)

### 1. Backend Setup
```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Run database migrations
alembic upgrade head

# 4. Start backend server
uvicorn app.main:app --reload --port 8000
```
- Open Swagger Docs: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Run Vite development server
npm run dev
```
- Open Web Application: `http://localhost:5173`

---

## 📁 Project Structure

```
WorkforceOS/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers & dependencies
│   │   ├── core/         # Async database session & security JWT handlers
│   │   ├── models/       # SQLAlchemy 2.0 ORM models with UUID PKs & SoftDelete
│   │   ├── repositories/ # Async data access layer
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Business logic layer
│   │   └── main.py       # FastAPI application entry point
│   ├── migrations/       # Alembic database migrations
│   ├── requirements.txt  # Backend Python dependencies
│   └── .env.example      # Environment variables template
└── frontend/
    ├── src/
    │   ├── api/          # Axios client & endpoint wrappers
    │   ├── components/   # UI components (Sidebar, TopBar, StatCard, Modal)
    │   ├── context/      # React AuthContext provider
    │   ├── pages/        # Dashboard, Employees, Departments, Attendance, Leave, Insights
    │   ├── types/        # TypeScript interface definitions
    │   ├── App.tsx       # Main router setup
    │   └── index.css     # Glassmorphism design system & CSS variables
    └── vite.config.ts    # Vite configuration & API proxy
```
