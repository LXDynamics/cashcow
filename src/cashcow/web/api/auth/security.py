"""Security utilities for authentication and authorization."""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import hashlib
import hmac
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import (
    User,
    TokenData,
    Permission,
    UserRole,
    get_permissions_for_role,
    has_permission,
)


# Security configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # TODO: Move to config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
API_KEY_LENGTH = 32

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for token authentication
security = HTTPBearer()


class SecurityConfig:
    """Security configuration."""
    
    def __init__(self):
        # TODO: Load from environment or config file
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
        self.api_key_length = API_KEY_LENGTH
        
        # Rate limiting configuration
        self.rate_limit_requests = 100
        self.rate_limit_window_minutes = 15
        
        # Login attempt limits
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 15


config = SecurityConfig()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return sum([has_upper, has_lower, has_digit, has_special]) >= 3


def create_access_token(
    user_id: str,
    email: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.access_token_expire_minutes)
    
    permissions = get_permissions_for_role(role)
    
    to_encode = {
        "user_id": user_id,
        "email": email,
        "role": role.value,
        "permissions": [p.value for p in permissions],
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "token_type": "access",
    }
    
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)
    return encoded_jwt


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=config.refresh_token_expire_days)
    
    to_encode = {
        "user_id": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "token_type": "refresh",
    }
    
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[config.algorithm])
        
        # Check token type
        if payload.get("token_type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.now(timezone.utc).timestamp() > exp:
            return None
        
        if token_type == "access":
            # For access tokens, return full TokenData
            # Convert string values back to enums
            role = UserRole(payload.get("role", "user"))
            permissions = [Permission(p) for p in payload.get("permissions", [])]
            
            return TokenData(
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                role=role,
                permissions=permissions,
                exp=exp,
                iat=payload.get("iat", 0),
                token_type=token_type,
            )
        else:
            # For refresh tokens, return minimal data
            return TokenData(
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                role=UserRole.USER,  # Will be updated from database
                permissions=[],
                exp=exp,
                iat=payload.get("iat", 0),
                token_type=token_type,
            )
    
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure random API key."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(config.api_key_length))


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hmac.compare_digest(hash_api_key(api_key), hashed_key)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, identifier: str, limit: int, window_minutes: int) -> bool:
        """Check if request is allowed based on rate limits."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        if identifier in self._requests:
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > window_start
            ]
        else:
            self._requests[identifier] = []
        
        # Check if under limit
        if len(self._requests[identifier]) >= limit:
            return False
        
        # Add current request
        self._requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str, limit: int, window_minutes: int) -> int:
        """Get remaining requests in the current window."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        
        if identifier not in self._requests:
            return limit
        
        recent_requests = [
            req_time for req_time in self._requests[identifier]
            if req_time > window_start
        ]
        
        return max(0, limit - len(recent_requests))


# Global rate limiter instance
rate_limiter = RateLimiter()


# Authentication dependencies for FastAPI

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials, "access")
    if token_data is None:
        raise credentials_exception
    
    return token_data


async def get_current_user_from_api_key(
    request: Request,
) -> Optional[TokenData]:
    """Get current user from API key header."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    # Import here to avoid circular imports
    from .database import db
    
    # Verify API key
    api_key_obj = await db.verify_api_key(api_key)
    if not api_key_obj:
        return None
    
    # Get user data
    user = await db.get_user(api_key_obj.user_id)
    if not user or not user.is_active:
        return None
    
    # Create TokenData from API key
    return TokenData(
        user_id=user.id,
        email=user.email,
        role=user.role,
        permissions=api_key_obj.permissions,  # Use API key permissions, not role permissions
        exp=int((datetime.utcnow() + timedelta(hours=24)).timestamp()),  # API keys don't expire like tokens
        iat=int(datetime.utcnow().timestamp()),
        token_type="api_key",
    )


async def get_current_user(
    request: Request,
    token_user: Optional[TokenData] = Depends(get_current_user_from_token),
) -> TokenData:
    """Get current user from either JWT token or API key."""
    # Try API key first (if present)
    api_key_user = await get_current_user_from_api_key(request)
    if api_key_user:
        return api_key_user
    
    # Fall back to JWT token
    if token_user:
        return token_user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


def require_permission(required_permission: Permission):
    """Dependency factory for permission-based access control."""
    
    async def permission_dependency(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission.value}' required",
            )
        return current_user
    
    return permission_dependency


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control."""
    
    async def role_dependency(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required",
            )
        return current_user
    
    return role_dependency


def require_admin():
    """Dependency for admin-only access."""
    return require_role(UserRole.ADMIN)


async def rate_limit_dependency(request: Request):
    """Rate limiting dependency."""
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not rate_limiter.is_allowed(
        client_ip,
        config.rate_limit_requests,
        config.rate_limit_window_minutes,
    ):
        remaining = rate_limiter.get_remaining(
            client_ip,
            config.rate_limit_requests,
            config.rate_limit_window_minutes,
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(config.rate_limit_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(
                    int((datetime.utcnow() + timedelta(minutes=config.rate_limit_window_minutes)).timestamp())
                ),
            },
        )


class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response