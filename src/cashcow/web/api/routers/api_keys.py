"""API key management router."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query

from ..auth.models import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
    APIKeyUsageStats,
    TokenData,
    Permission,
)
from ..auth.security import (
    get_current_user,
    require_permission,
)
from ..auth.database import db, APIKeyNotFoundError


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: TokenData = Depends(require_permission(Permission.API_KEY_MANAGE)),
) -> List[APIKeyResponse]:
    """List all API keys for the current user."""
    
    api_keys = await db.list_user_api_keys(current_user.user_id)
    
    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            description=key.description,
            permissions=key.permissions,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used=key.last_used,
            usage_count=key.usage_count,
            is_active=key.is_active,
        )
        for key in api_keys
    ]


@router.post("", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: TokenData = Depends(require_permission(Permission.API_KEY_MANAGE)),
) -> APIKeyWithSecret:
    """Create a new API key for the current user."""
    
    # Validate permissions - users can only grant permissions they have
    invalid_permissions = []
    for permission in api_key_create.permissions:
        if permission not in current_user.permissions:
            invalid_permissions.append(permission.value)
    
    if invalid_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot grant permissions you don't have: {', '.join(invalid_permissions)}",
        )
    
    # Validate expiration date
    if api_key_create.expires_at:
        if api_key_create.expires_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiration date must be in the future",
            )
        
        # Limit API key expiration to 1 year
        max_expiry = datetime.utcnow() + timedelta(days=365)
        if api_key_create.expires_at > max_expiry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key expiration cannot exceed 1 year",
            )
    
    try:
        api_key = await db.create_api_key(current_user.user_id, api_key_create)
        
        return APIKeyWithSecret(
            id=api_key.id,
            name=api_key.name,
            description=api_key.description,
            permissions=api_key.permissions,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used=api_key.last_used,
            usage_count=api_key.usage_count,
            is_active=api_key.is_active,
            key=getattr(api_key, '_original_key', ''),  # The actual key, only shown once
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: TokenData = Depends(require_permission(Permission.API_KEY_MANAGE)),
) -> APIKeyResponse:
    """Get details of a specific API key."""
    
    api_key = await db.get_api_key(key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    # Check if the API key belongs to the current user
    if api_key.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this API key",
        )
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        permissions=api_key.permissions,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used=api_key.last_used,
        usage_count=api_key.usage_count,
        is_active=api_key.is_active,
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: TokenData = Depends(require_permission(Permission.API_KEY_MANAGE)),
) -> Dict[str, str]:
    """Revoke (deactivate) an API key."""
    
    # First check if the key exists and belongs to the user
    api_key = await db.get_api_key(key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    if api_key.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this API key",
        )
    
    success = await db.revoke_api_key(key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )
    
    return {"message": "API key revoked successfully"}


@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage(
    key_id: str,
    current_user: TokenData = Depends(require_permission(Permission.API_KEY_MANAGE)),
) -> APIKeyUsageStats:
    """Get usage statistics for an API key."""
    
    api_key = await db.get_api_key(key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    if api_key.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this API key",
        )
    
    # For now, return basic usage stats
    # In a full implementation, you would track detailed usage logs
    return APIKeyUsageStats(
        total_requests=api_key.usage_count,
        requests_last_24h=0,  # TODO: Implement detailed usage tracking
        requests_last_7d=0,
        requests_last_30d=0,
        last_used=api_key.last_used,
        endpoints_used=[],  # TODO: Track which endpoints were accessed
    )


@router.post("/{key_id}/regenerate", response_model=APIKeyWithSecret)
async def regenerate_api_key(
    key_id: str,
    current_user: TokenData = Depends(require_permission(Permission.API_KEY_MANAGE)),
) -> APIKeyWithSecret:
    """Regenerate an API key (creates new key with same metadata)."""
    
    # Get existing API key
    existing_key = await db.get_api_key(key_id)
    
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    if existing_key.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to regenerate this API key",
        )
    
    # Revoke old key
    await db.revoke_api_key(key_id)
    
    # Create new key with same metadata
    api_key_create = APIKeyCreate(
        name=existing_key.name,
        description=existing_key.description,
        permissions=existing_key.permissions,
        expires_at=existing_key.expires_at,
    )
    
    try:
        new_api_key = await db.create_api_key(current_user.user_id, api_key_create)
        
        return APIKeyWithSecret(
            id=new_api_key.id,
            name=new_api_key.name,
            description=new_api_key.description,
            permissions=new_api_key.permissions,
            created_at=new_api_key.created_at,
            expires_at=new_api_key.expires_at,
            last_used=new_api_key.last_used,
            usage_count=new_api_key.usage_count,
            is_active=new_api_key.is_active,
            key=getattr(new_api_key, '_original_key', ''),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate API key: {str(e)}",
        )


@router.get("/validate/{api_key}")
async def validate_api_key(
    api_key: str,
    current_user: TokenData = Depends(get_current_user),
) -> Dict[str, Any]:
    """Validate an API key and return its information."""
    
    # This endpoint is mainly for debugging/testing
    # In production, API key validation would be done internally
    
    validated_key = await db.verify_api_key(api_key)
    
    if not validated_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired API key",
        )
    
    # Only allow users to validate their own keys
    if validated_key.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to validate this API key",
        )
    
    return {
        "valid": True,
        "key_id": validated_key.id,
        "name": validated_key.name,
        "permissions": [p.value for p in validated_key.permissions],
        "expires_at": validated_key.expires_at,
        "usage_count": validated_key.usage_count,
    }