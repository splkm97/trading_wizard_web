"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.core.config import settings
from src.core.logging import logger
from src.db.database import init_db

# Scheduler instance (module-level for lifecycle management)
_scheduler = None


def init_scheduler():
    """Initialize APScheduler for background tasks."""
    global _scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        import pytz

        from src.services.price_updater import scheduled_price_update

        _scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Seoul"))

        # Schedule price update job at 15:35 KST (5 minutes after market close)
        _scheduler.add_job(
            scheduled_price_update,
            CronTrigger(hour=15, minute=35, timezone=pytz.timezone("Asia/Seoul")),
            id="price_update",
            name="Daily Closing Price Update",
            replace_existing=True,
        )

        _scheduler.start()
        logger.info("Scheduler started: price update scheduled at 15:35 KST")

    except ImportError as e:
        logger.warning(f"APScheduler not available, skipping scheduler init: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")


def shutdown_scheduler():
    """Shutdown APScheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Trading Wizard Web API...")
    init_db()
    logger.info("Database initialized")

    # Initialize scheduler
    init_scheduler()

    yield

    # Shutdown
    shutdown_scheduler()
    logger.info("Shutting down Trading Wizard Web API...")


app = FastAPI(
    title="Trading Wizard Web API",
    description="Web API for trading data management, backtesting, and portfolio visualization",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Trading Wizard Web API",
        "version": "0.1.0",
        "docs": "/docs",
    }
