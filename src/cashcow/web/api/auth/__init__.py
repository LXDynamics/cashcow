"""
CashCow Web API Authentication - User authentication and authorization.
"""

from .models import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenData,
    LoginRequest,
    APIKey,
    APIKeyCreate,
    APIKeyResponse,
    Permission,
    UserRole,
)

from .security import (
    get_current_user,
    require_permission,
    require_role,
    require_admin,
    create_access_token,
    create_refresh_token,
    verify_token,
)

from .database import db

from .permissions import (
    PermissionChecker,
    require_entity_access,
    require_report_access,
    require_calculation_access,
)

__all__ = [
    # Models
    "User",
    "UserCreate", 
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    "APIKey",
    "APIKeyCreate",
    "APIKeyResponse",
    "Permission",
    "UserRole",
    
    # Security functions
    "get_current_user",
    "require_permission",
    "require_role",
    "require_admin",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    
    # Database
    "db",
    
    # Permissions
    "PermissionChecker",
    "require_entity_access",
    "require_report_access", 
    "require_calculation_access",
]