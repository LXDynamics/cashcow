"""Permission system for CashCow web API."""

from typing import List, Set, Optional
from fastapi import HTTPException, status, Depends, Request

from .models import (
    Permission,
    UserRole,
    TokenData,
    get_permissions_for_role,
    has_permission,
)
from .security import get_current_user
from .database import db


class PermissionChecker:
    """Permission checking utilities."""
    
    @staticmethod
    def check_entity_access(
        current_user: TokenData,
        entity_user_id: Optional[str] = None,
        required_permission: Permission = Permission.READ_ENTITIES,
    ) -> bool:
        """Check if user can access a specific entity."""
        
        # Check if user has the required permission
        if required_permission not in current_user.permissions:
            return False
        
        # Admins can access all entities
        if current_user.role == UserRole.ADMIN:
            return True
        
        # For non-admins, check entity ownership
        if entity_user_id and entity_user_id != current_user.user_id:
            # User can only access their own entities unless they're admin
            return False
        
        return True
    
    @staticmethod
    def check_report_access(
        current_user: TokenData,
        report_scope: str = "user",  # "user" or "system"
    ) -> bool:
        """Check if user can access reports."""
        
        if report_scope == "system":
            # System-wide reports require admin access
            return (
                Permission.ADMIN_ACCESS in current_user.permissions
                and Permission.GENERATE_REPORTS in current_user.permissions
            )
        
        # User-scope reports just need report permission
        return Permission.READ_REPORTS in current_user.permissions
    
    @staticmethod
    def check_calculation_access(
        current_user: TokenData,
        calculation_scope: str = "user",  # "user" or "system"
    ) -> bool:
        """Check if user can run calculations."""
        
        if calculation_scope == "system":
            # System-wide calculations require admin access
            return (
                Permission.ADMIN_ACCESS in current_user.permissions
                and Permission.RUN_CALCULATIONS in current_user.permissions
            )
        
        # User-scope calculations just need calculation permission
        return Permission.RUN_CALCULATIONS in current_user.permissions


def require_entity_access(
    required_permission: Permission = Permission.READ_ENTITIES,
    allow_own_only: bool = True,
):
    """Dependency factory for entity-based access control."""
    
    async def entity_access_dependency(
        request: Request,
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        
        # Check basic permission
        if required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission.value}' required",
            )
        
        # For entity-specific operations, check ownership
        if allow_own_only and current_user.role != UserRole.ADMIN:
            # Extract entity ID from path if present
            entity_id = request.path_params.get("entity_id")
            
            if entity_id:
                # TODO: Implement entity ownership check
                # For now, we'll assume all entities belong to the current user
                # In a full implementation, you would query the entity database
                pass
        
        return current_user
    
    return entity_access_dependency


def require_report_access(system_wide: bool = False):
    """Dependency factory for report access control."""
    
    async def report_access_dependency(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        
        scope = "system" if system_wide else "user"
        
        if not PermissionChecker.check_report_access(current_user, scope):
            if system_wide:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required for system-wide reports",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Report access permission required",
                )
        
        return current_user
    
    return report_access_dependency


def require_calculation_access(system_wide: bool = False):
    """Dependency factory for calculation access control."""
    
    async def calculation_access_dependency(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        
        scope = "system" if system_wide else "user"
        
        if not PermissionChecker.check_calculation_access(current_user, scope):
            if system_wide:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required for system-wide calculations",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Calculation permission required",
                )
        
        return current_user
    
    return calculation_access_dependency


def filter_entities_by_access(
    entities: List[dict],
    current_user: TokenData,
) -> List[dict]:
    """Filter entity list based on user access permissions."""
    
    # Admins can see all entities
    if current_user.role == UserRole.ADMIN:
        return entities
    
    # Regular users can only see their own entities
    # This assumes entities have a 'user_id' or 'created_by' field
    filtered_entities = []
    
    for entity in entities:
        entity_owner = entity.get("user_id") or entity.get("created_by")
        
        if entity_owner == current_user.user_id:
            filtered_entities.append(entity)
    
    return filtered_entities


class ResourcePermissionChecker:
    """Check permissions for specific resources."""
    
    @staticmethod
    async def check_user_management_permission(
        current_user: TokenData,
        target_user_id: str,
        operation: str,  # "read", "write", "delete"
    ) -> bool:
        """Check if user can perform operation on target user."""
        
        # Users can always read/write their own profile
        if target_user_id == current_user.user_id and operation in ["read", "write"]:
            return True
        
        # Admin operations require admin permissions
        permission_map = {
            "read": Permission.READ_USERS,
            "write": Permission.WRITE_USERS,
            "delete": Permission.DELETE_USERS,
        }
        
        required_permission = permission_map.get(operation)
        
        if not required_permission:
            return False
        
        return required_permission in current_user.permissions
    
    @staticmethod
    async def check_api_key_permission(
        current_user: TokenData,
        api_key_id: str,
        operation: str,  # "read", "write", "delete"
    ) -> bool:
        """Check if user can perform operation on API key."""
        
        # Get API key to check ownership
        api_key = await db.get_api_key(api_key_id)
        
        if not api_key:
            return False
        
        # Users can manage their own API keys if they have the permission
        if (
            api_key.user_id == current_user.user_id
            and Permission.API_KEY_MANAGE in current_user.permissions
        ):
            return True
        
        # Admins can manage all API keys
        return (
            Permission.ADMIN_ACCESS in current_user.permissions
            and Permission.API_KEY_MANAGE in current_user.permissions
        )


# Permission decorators for route handlers

def check_permission(permission: Permission):
    """Decorator to check permissions in route handlers."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            
            if not current_user or permission not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission.value}' required",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def check_role(role: UserRole):
    """Decorator to check user role in route handlers."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            
            if not current_user or (
                current_user.role != role and current_user.role != UserRole.ADMIN
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role.value}' required",
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Utility functions for permission checking

def get_user_effective_permissions(user_role: UserRole) -> Set[Permission]:
    """Get all effective permissions for a user role."""
    return set(get_permissions_for_role(user_role))


def can_user_grant_permission(
    granter_role: UserRole,
    permission: Permission,
) -> bool:
    """Check if a user can grant a specific permission to others."""
    
    # Only admins can grant permissions
    if granter_role != UserRole.ADMIN:
        return False
    
    # Admins can grant any permission
    return True


def validate_permission_grant(
    granter_permissions: List[Permission],
    permissions_to_grant: List[Permission],
) -> List[Permission]:
    """Validate that a user can grant the requested permissions."""
    
    invalid_permissions = []
    
    for permission in permissions_to_grant:
        if permission not in granter_permissions:
            invalid_permissions.append(permission)
    
    return invalid_permissions