# pyrefly: ignore [parse-error]
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select

from app.core.database import engine
from app.api.routes.auth import router as auth_router
from app.api.routes.departments import router as departments_router
from app.api.routes.employees import router as employees_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.leave import router as leave_router
from app.api.routes.insights import router as insights_router
from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.payroll import router as payroll_router

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workforce_mgmt")


# ─── Security Headers Middleware ────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security-hardening HTTP response headers to every response.
    Prevents clickjacking, MIME sniffing, and enforces strict transport security.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        # Remove server identification
        response.headers.pop("server", None)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI app.
    
    Performs startup verification of the database connection.
    """
    logger.info("Initializing application startup validations...")
    try:
        # Simple query to verify connectivity to database on startup
        async with engine.connect() as conn:
            await conn.execute(select(1))
        logger.info("Database connection validation successful.")
    except Exception as e:
        logger.critical(f"Database connection validation failed: {e}")
        # We do not crash the app immediately here to allow the process to start
        # and respond to healthchecks, but logging it as CRITICAL is essential.
        
    yield
    
    logger.info("Application shutdown sequence initiated.")
    # Dispose of engine connection pool on shutdown
    await engine.dispose()
    logger.info("Engine connection pool disposed.")


# Initialize the FastAPI App
app = FastAPI(
    title="AI Workforce Management System",
    description="Backend API for managing departments, employee onboarding, profiles, and audit logging.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ─── CORS Middleware ────────────────────────────────────────────────────────
# Origins read from env — never wildcard in production
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,
)

# ─── Security Headers ───────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ─── Trusted Host (blocks Host header injection) ────────────────────────────
_trusted = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,*")
TRUSTED_HOSTS = [h.strip() for h in _trusted.split(",") if h.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

# ─── Register API Routers ───────────────────────────────────────────────────
# Mount under /api prefix to align with oauth2 endpoint setup
app.include_router(auth_router, prefix="/api")
app.include_router(departments_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(leave_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(audit_logs_router, prefix="/api")
app.include_router(payroll_router, prefix="/api")


@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the uptime status of the API service."
)
async def health_check():
    """Simple healthcheck returning OK status."""
    return {"status": "healthy", "service": "AI Workforce Management System"}

