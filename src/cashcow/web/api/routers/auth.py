"""Authentication router for login, logout, and token management."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from ..auth.models import (
    LoginRequest,
    Token,
    TokenData,
    ChangePasswordRequest,
    RefreshTokenRequest,
    UserResponse,
)
from ..auth.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    validate_password_strength,
    get_current_user,
    rate_limit_dependency,
    config,
)
from ..auth.database import db


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
) -> Token:
    """Authenticate user and return JWT tokens."""
    
    # Authenticate user
    user = await db.authenticate_user(login_request.email, login_request.password)
    
    if not user:
        # Log failed login attempt
        await _log_login_attempt(
            email=login_request.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            success=False,
            failure_reason="Invalid credentials",
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )
    
    # Check if user is locked
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked until {user.locked_until}",
        )
    
    # Create tokens
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )
    
    refresh_token = create_refresh_token(
        user_id=user.id,
        email=user.email,
    )
    
    # Log successful login
    await _log_login_attempt(
        email=login_request.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        success=True,
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=config.access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    current_user: TokenData = Depends(get_current_user),
) -> Dict[str, str]:
    """Logout user by blacklisting the current token."""
    
    # In a full implementation, we would extract the JTI (JWT ID) from the token
    # and add it to a blacklist. For now, we'll just return success.
    # TODO: Implement token blacklisting with JTI
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    _: None = Depends(rate_limit_dependency),
) -> Token:
    """Refresh access token using refresh token."""
    
    # Verify refresh token
    token_data = verify_token(refresh_request.refresh_token, "refresh")
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Get user to ensure they still exist and are active
    user = await db.get_user(token_data.user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new access token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )
    
    # Optionally create new refresh token for token rotation
    new_refresh_token = create_refresh_token(
        user_id=user.id,
        email=user.email,
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=config.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
) -> UserResponse:
    """Get current user information."""
    
    # Get full user data from database
    user = await db.get_user(current_user.user_id)
    
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


@router.post("/change-password")
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
) -> Dict[str, str]:
    """Change user password."""
    
    # Get current user data
    user = await db.get_user(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # For password verification, we need to read the hashed password from the database
    # This is a bit awkward with our current structure, but works for now
    user_with_password = await db.get_user_by_email(user.email)
    if not user_with_password:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify current password
    # We need to access the password hash directly from the database
    # This is a limitation of our current model structure
    users_data = await db._read_json_file(db.users_file)
    user_data = users_data.get(user.id)
    
    if not user_data or not verify_password(password_request.current_password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Validate new password strength
    if not validate_password_strength(password_request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements. Must be at least 8 characters with 3 of: uppercase, lowercase, numbers, special characters",
        )
    
    # Change password
    success = await db.change_password(user.id, password_request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )
    
    return {"message": "Password changed successfully"}


@router.get("/status")
async def auth_status() -> Dict[str, Any]:
    """Get authentication system status."""
    
    return {
        "service": "authentication",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token_expiry_minutes": config.access_token_expire_minutes,
        "refresh_token_expiry_days": config.refresh_token_expire_days,
    }


async def _log_login_attempt(
    email: str,
    ip_address: str,
    user_agent: str,
    success: bool,
    failure_reason: str = None,
):
    """Log login attempt for security monitoring."""
    
    # Read current login attempts
    login_attempts = await db._read_json_file(db.login_attempts_file)
    
    # Add new attempt
    attempt_id = f"{datetime.utcnow().isoformat()}_{email}_{ip_address}"
    
    attempt_data = {
        "email": email,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "failure_reason": failure_reason,
    }
    
    login_attempts[attempt_id] = attempt_data
    
    # Keep only last 1000 attempts to prevent file from growing too large
    if len(login_attempts) > 1000:
        # Sort by timestamp and keep newest 1000
        sorted_attempts = sorted(
            login_attempts.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        login_attempts = dict(sorted_attempts[:1000])
    
    await db._write_json_file(db.login_attempts_file, login_attempts)