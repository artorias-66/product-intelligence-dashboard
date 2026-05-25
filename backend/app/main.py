"""FastAPI application entry point with all routers mounted."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables, get_db, SessionLocal
from app.routers import (
    upload,
    jobs,
    products,
    dashboard,
    competitor_prices,
    alerts,
    title_enhancement,
)
from app.schemas import HealthResponse, MessageResponse

from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    create_tables()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api prefix
app.include_router(upload.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(competitor_prices.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(title_enhancement.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
@app.head("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint that also verifies database connectivity."""
    db_status = "disconnected"
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        database=db_status,
    )


@app.get("/api", tags=["Root"])
def api_root():
    """API root with basic info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.post("/api/seed", response_model=MessageResponse, tags=["Admin"])
def seed_database():
    """Seed the database with sample data."""
    from app.seed import run_seed

    db = SessionLocal()
    try:
        result = run_seed(db)
        return MessageResponse(message=result)
    finally:
        db.close()


@app.post("/api/reset", response_model=MessageResponse, tags=["Admin"])
def reset_database():
    """Drop all tables and recreate them. WARNING: Destroys all data."""
    from app.database import drop_tables

    drop_tables()
    create_tables()
    return MessageResponse(message="Database reset complete. All tables recreated.")
