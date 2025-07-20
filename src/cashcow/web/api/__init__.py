"""
CashCow Web API - FastAPI application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .middleware import (
    LoggingMiddleware, 
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    CORSSecurityMiddleware
)
from .exceptions import (
    validation_exception_handler,
    general_exception_handler,
    CashCowAPIException
)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="CashCow API",
        description="REST API for CashCow cash flow modeling system with JWT authentication",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add middleware in order (last added = first executed)
    # Rate limiting should be first to prevent abuse
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Secure CORS configuration
    app.add_middleware(
        CORSSecurityMiddleware,
        allowed_origins=[
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080"
        ]
    )
    
    # Add exception handlers
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Include authentication routers
    from .routers import auth, users, api_keys
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(api_keys.router, prefix="/api")
    
    return app