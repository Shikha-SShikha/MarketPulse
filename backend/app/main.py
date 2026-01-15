"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import router as api_router
from app.scheduler import init_scheduler, shutdown_scheduler
from app.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware, RateLimitMiddleware


def setup_logging():
    """Configure structured logging."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting STM Intelligence Brief System")
    logger.info(f"Environment: {'development' if 'dev' in get_settings().curator_token else 'production'}")

    # Initialize background scheduler
    init_scheduler()

    yield

    # Shutdown scheduler
    shutdown_scheduler()
    logger.info("Shutting down STM Intelligence Brief System")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="STM Intelligence Brief System",
        description="Market/competitive intelligence platform for STM publishing sales teams",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware (order matters - first added = outermost)
    # Error handling should be outermost to catch all errors
    app.add_middleware(ErrorHandlingMiddleware)

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting for admin endpoints
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    # CORS configuration
    origins = [origin.strip() for origin in settings.allowed_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Health check endpoint
    @app.get("/health", tags=["system"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {"status": "ok", "version": "1.0.0"}

    # Register API routes
    app.include_router(api_router, tags=["api"])

    logger.info(f"CORS configured for origins: {origins}")
    logger.info("Application startup complete")

    return app


app = create_app()
