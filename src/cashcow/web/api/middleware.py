"""
CashCow Web API - Middleware configuration.
"""

import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request/response information with user context.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and log timing/status information.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint function
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        # Extract user information if available
        user_info = "anonymous"
        auth_header = request.headers.get("authorization")
        api_key_header = request.headers.get("x-api-key")
        
        if auth_header or api_key_header:
            try:
                # Try to get user info from token/API key
                # This is a simplified version - in production you might want more details
                user_info = "authenticated"
            except Exception:
                user_info = "auth_failed"
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request with context
        logger.info(
            f"Request: {request.method} {request.url} - "
            f"User: {user_info} - IP: {client_ip}"
        )
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"Processed in {process_time:.3f}s - "
            f"User: {user_info} - IP: {client_ip}"
        )
        
        # Add processing time to response headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint function
            
        Returns:
            Response with security headers
        """
        response: Response = await call_next(request)
        
        # Add comprehensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = {}
    
    async def dispatch(self, request: Request, call_next):
        """
        Apply rate limiting based on client IP.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint function
            
        Returns:
            Response or HTTPException if rate limited
        """
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests (older than 1 minute)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > cutoff
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            # Create rate limit response
            response = Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now + timedelta(minutes=1)).timestamp())),
                    "Retry-After": "60"
                }
            )
            return response
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = max(0, self.requests_per_minute - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        
        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with security considerations.
    """
    
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["http://localhost:3000", "http://localhost:8080"]
    
    async def dispatch(self, request: Request, call_next):
        """
        Handle CORS with security considerations.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint function
            
        Returns:
            Response with CORS headers
        """
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        # Add CORS headers if origin is allowed
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-API-Key, X-Requested-With"
            )
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return response