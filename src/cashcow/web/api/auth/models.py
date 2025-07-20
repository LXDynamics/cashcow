"""Authentication models for CashCow web API."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    """User roles for role-based access control."""
    
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class Permission(str, Enum):
    """System permissions."""
    
    # Entity permissions
    READ_ENTITIES = "read_entities"
    WRITE_ENTITIES = "write_entities"
    DELETE_ENTITIES = "delete_entities"
    
    # User management permissions
    READ_USERS = "read_users"
    WRITE_USERS = "write_users"
    DELETE_USERS = "delete_users"
    
    # System permissions
    ADMIN_ACCESS = "admin_access"
    API_KEY_MANAGE = "api_key_manage"
    
    # Financial permissions
    READ_REPORTS = "read_reports"
    GENERATE_REPORTS = "generate_reports"
    RUN_CALCULATIONS = "run_calculations"


class UserBase(BaseModel):
    """Base user model with common fields."""
    
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    """Model for creating a new user."""
    
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Model for updating user information."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Complete user model with ID and timestamps."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


class UserResponse(BaseModel):
    """User model for API responses (no sensitive data)."""
    
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request model."""
    
    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """JWT token response model."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data."""
    
    user_id: str
    email: str
    role: UserRole
    permissions: List[Permission]
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    token_type: str = "access"  # access or refresh


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class APIKeyBase(BaseModel):
    """Base API key model."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[Permission] = []
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    """Model for creating a new API key."""
    pass


class APIKey(APIKeyBase):
    """Complete API key model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    key_hash: str  # Hashed version of the actual key
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True


class APIKeyResponse(BaseModel):
    """API key response model."""
    
    id: str
    name: str
    description: Optional[str]
    permissions: List[Permission]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    is_active: bool


class APIKeyWithSecret(APIKeyResponse):
    """API key response with the actual key (only returned on creation)."""
    
    key: str  # The actual API key (only shown once)


class APIKeyUsageStats(BaseModel):
    """API key usage statistics."""
    
    total_requests: int
    requests_last_24h: int
    requests_last_7d: int
    requests_last_30d: int
    last_used: Optional[datetime]
    endpoints_used: List[str]


class LoginAttempt(BaseModel):
    """Login attempt tracking."""
    
    email: str
    ip_address: str
    user_agent: str
    success: bool
    timestamp: datetime
    failure_reason: Optional[str] = None


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_ENTITIES,
        Permission.WRITE_ENTITIES,
        Permission.DELETE_ENTITIES,
        Permission.READ_USERS,
        Permission.WRITE_USERS,
        Permission.DELETE_USERS,
        Permission.ADMIN_ACCESS,
        Permission.API_KEY_MANAGE,
        Permission.READ_REPORTS,
        Permission.GENERATE_REPORTS,
        Permission.RUN_CALCULATIONS,
    ],
    UserRole.USER: [
        Permission.READ_ENTITIES,
        Permission.WRITE_ENTITIES,
        Permission.API_KEY_MANAGE,
        Permission.READ_REPORTS,
        Permission.GENERATE_REPORTS,
        Permission.RUN_CALCULATIONS,
    ],
    UserRole.READONLY: [
        Permission.READ_ENTITIES,
        Permission.READ_REPORTS,
    ],
}


def get_permissions_for_role(role: UserRole) -> List[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if a user role has a specific permission."""
    user_permissions = get_permissions_for_role(user_role)
    return required_permission in user_permissions