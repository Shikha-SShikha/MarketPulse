"""Middleware for request/response processing."""

import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions import AppException

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and outgoing responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid4())[:8]
        request.state.request_id = request_id

        # Log request
        start_time = time.time()
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""

        logger.info(
            f"[{request_id}] {method} {path}{f'?{query}' if query else ''}"
        )

        # Process request
        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] {method} {path} -> {response.status_code} ({duration:.1f}ms)"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] {method} {path} -> ERROR ({duration:.1f}ms): {str(e)}"
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Convert exceptions to consistent JSON error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AppException as e:
            logger.warning(f"App exception: {e.message}", extra={"details": e.details})
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.message,
                    "status": e.status_code,
                    "details": e.details if e.details else None,
                },
            )
        except Exception as e:
            logger.exception(f"Unhandled exception: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "status": 500,
                },
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting for admin endpoints."""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}  # IP -> list of timestamps

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate limit admin endpoints
        if not request.url.path.startswith("/admin"):
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries and count recent requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if current_time - t < 60
            ]
        else:
            self.requests[client_ip] = []

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded. Please try again later.",
                    "status": 429,
                },
            )

        # Record this request
        self.requests[client_ip].append(current_time)

        return await call_next(request)
