# pyrefly: ignore [parse-error]
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from app.core.database import engine
from app.api.routes.auth import router as auth_router
from app.api.routes.departments import router as departments_router
from app.api.routes.employees import router as employees_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.leave import router as leave_router

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workforce_mgmt")


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

# Configure CORS Middleware
# Allows request origin validation for UI integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
# Mount under /api prefix to align with oauth2 endpoint setup
app.include_router(auth_router, prefix="/api")
app.include_router(departments_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(leave_router, prefix="/api")


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
