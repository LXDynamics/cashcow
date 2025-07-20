"""User management router."""

from typing import List, Dict
from fastapi import APIRouter, HTTPException, status, Depends, Query

from ..auth.models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenData,
    Permission,
    UserRole,
)
from ..auth.security import (
    get_current_user,
    require_permission,
    require_admin,
    validate_password_strength,
)
from ..auth.database import db, UserNotFoundError, DatabaseError


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    current_user: TokenData = Depends(require_permission(Permission.READ_USERS)),
) -> List[UserResponse]:
    """List all users (admin only)."""
    
    users = await db.list_users(skip=skip, limit=limit)
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )
        for user in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: TokenData = Depends(require_permission(Permission.WRITE_USERS)),
) -> UserResponse:
    """Create a new user (admin only)."""
    
    # Validate password strength
    if not validate_password_strength(user_create.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements. Must be at least 8 characters with 3 of: uppercase, lowercase, numbers, special characters",
        )
    
    # Only admins can create other admins
    if user_create.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create admin users",
        )
    
    try:
        user = await db.create_user(user_create)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )
    
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
) -> UserResponse:
    """Get user details by ID."""
    
    # Users can view their own profile, admins can view anyone
    if user_id != current_user.user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )
    
    user = await db.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
) -> UserResponse:
    """Update user information."""
    
    # Users can update their own profile (except role), admins can update anyone
    if user_id != current_user.user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    
    # Non-admins cannot change roles
    if user_update.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles",
        )
    
    # Only admins can create other admins
    if user_update.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign admin role",
        )
    
    try:
        user = await db.update_user(user_id, user_update)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )
    
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.DELETE_USERS)),
) -> Dict[str, str]:
    """Delete a user (admin only)."""
    
    # Prevent self-deletion
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    success = await db.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: TokenData = Depends(require_admin()),
) -> Dict[str, str]:
    """Activate a user account (admin only)."""
    
    user_update = UserUpdate(is_active=True)
    
    try:
        await db.update_user(user_id, user_update)
        return {"message": "User activated successfully"}
    
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: TokenData = Depends(require_admin()),
) -> Dict[str, str]:
    """Deactivate a user account (admin only)."""
    
    # Prevent self-deactivation
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    user_update = UserUpdate(is_active=False)
    
    try:
        await db.update_user(user_id, user_update)
        return {"message": "User deactivated successfully"}
    
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.get("/{user_id}/permissions", response_model=List[str])
async def get_user_permissions(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
) -> List[str]:
    """Get user permissions."""
    
    # Users can view their own permissions, admins can view anyone's
    if user_id != current_user.user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's permissions",
        )
    
    user = await db.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    from ..auth.models import get_permissions_for_role
    permissions = get_permissions_for_role(user.role)
    
    return [permission.value for permission in permissions]