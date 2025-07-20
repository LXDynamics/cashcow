"""File-based database for authentication data."""

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import aiofiles
from threading import Lock

from .models import (
    User,
    UserCreate,
    UserUpdate,
    APIKey,
    APIKeyCreate,
    LoginAttempt,
    UserRole,
    Permission,
    get_permissions_for_role,
)
from .security import get_password_hash, verify_password, generate_api_key, hash_api_key


class DatabaseError(Exception):
    """Database operation error."""
    pass


class UserNotFoundError(DatabaseError):
    """User not found error."""
    pass


class APIKeyNotFoundError(DatabaseError):
    """API key not found error."""
    pass


class FileDatabase:
    """Simple file-based database for authentication data."""
    
    def __init__(self, data_dir: str = "data/auth"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.api_keys_file = self.data_dir / "api_keys.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self.login_attempts_file = self.data_dir / "login_attempts.json"
        
        self._lock = Lock()
        
        # Initialize files if they don't exist
        self._init_files()
        
        # Create default admin user if no users exist
        if not self._has_users():
            self._create_default_admin()
    
    def _init_files(self):
        """Initialize database files if they don't exist."""
        files_to_init = [
            self.users_file,
            self.api_keys_file,
            self.sessions_file,
            self.login_attempts_file,
        ]
        
        for file_path in files_to_init:
            if not file_path.exists():
                with open(file_path, "w") as f:
                    json.dump({}, f)
    
    def _has_users(self) -> bool:
        """Check if any users exist."""
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
                return len(users) > 0
        except (FileNotFoundError, json.JSONDecodeError):
            return False
    
    def _create_default_admin(self):
        """Create default admin user for development."""
        admin_user = UserCreate(
            email="admin@cashcow.dev",
            full_name="Default Admin",
            password="changeme",
            role=UserRole.ADMIN,
        )
        
        # Create user synchronously during initialization
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        user_data = {
            "id": user_id,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "role": admin_user.role.value,
            "is_active": True,
            "password_hash": get_password_hash(admin_user.password),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        
        with open(self.users_file, "w") as f:
            json.dump({user_id: user_data}, f, indent=2)
    
    async def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file asynchronously."""
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def _write_json_file(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file asynchronously."""
        with self._lock:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(data, indent=2, default=str))
    
    # User management methods
    
    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        users = await self._read_json_file(self.users_file)
        
        # Check if email already exists
        for user_data in users.values():
            if user_data["email"] == user_create.email:
                raise DatabaseError("Email already registered")
        
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        user_data = {
            "id": user_id,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "role": user_create.role.value,
            "is_active": user_create.is_active,
            "password_hash": get_password_hash(user_create.password),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        
        users[user_id] = user_data
        await self._write_json_file(self.users_file, users)
        
        return self._user_from_dict(user_data)
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        users = await self._read_json_file(self.users_file)
        user_data = users.get(user_id)
        
        if not user_data:
            return None
        
        return self._user_from_dict(user_data)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        users = await self._read_json_file(self.users_file)
        
        for user_data in users.values():
            if user_data["email"] == email:
                return self._user_from_dict(user_data)
        
        return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> User:
        """Update user information."""
        users = await self._read_json_file(self.users_file)
        
        if user_id not in users:
            raise UserNotFoundError(f"User {user_id} not found")
        
        user_data = users[user_id]
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "role" and isinstance(value, UserRole):
                user_data[field] = value.value
            else:
                user_data[field] = value
        
        user_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        users[user_id] = user_data
        await self._write_json_file(self.users_file, users)
        
        return self._user_from_dict(user_data)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        users = await self._read_json_file(self.users_file)
        
        if user_id not in users:
            return False
        
        del users[user_id]
        await self._write_json_file(self.users_file, users)
        
        return True
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        users = await self._read_json_file(self.users_file)
        
        user_list = [self._user_from_dict(user_data) for user_data in users.values()]
        user_list.sort(key=lambda u: u.created_at)
        
        return user_list[skip:skip + limit]
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        # Check if user is locked
        if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
            return None
        
        # Verify password
        users = await self._read_json_file(self.users_file)
        user_data = users[user.id]
        
        if not verify_password(password, user_data["password_hash"]):
            # Increment failed attempts
            await self._increment_failed_attempts(user.id)
            return None
        
        # Reset failed attempts and update last login
        await self._reset_failed_attempts(user.id)
        await self._update_last_login(user.id)
        
        return user
    
    async def change_password(self, user_id: str, new_password: str) -> bool:
        """Change user password."""
        users = await self._read_json_file(self.users_file)
        
        if user_id not in users:
            return False
        
        users[user_id]["password_hash"] = get_password_hash(new_password)
        users[user_id]["updated_at"] = datetime.utcnow().isoformat()
        
        await self._write_json_file(self.users_file, users)
        return True
    
    async def _increment_failed_attempts(self, user_id: str):
        """Increment failed login attempts."""
        users = await self._read_json_file(self.users_file)
        
        if user_id in users:
            users[user_id]["failed_login_attempts"] += 1
            
            # Lock user if too many failed attempts
            if users[user_id]["failed_login_attempts"] >= 5:
                users[user_id]["locked_until"] = (
                    datetime.now(timezone.utc) + timedelta(minutes=15)
                ).isoformat()
            
            await self._write_json_file(self.users_file, users)
    
    async def _reset_failed_attempts(self, user_id: str):
        """Reset failed login attempts."""
        users = await self._read_json_file(self.users_file)
        
        if user_id in users:
            users[user_id]["failed_login_attempts"] = 0
            users[user_id]["locked_until"] = None
            await self._write_json_file(self.users_file, users)
    
    async def _update_last_login(self, user_id: str):
        """Update last login timestamp."""
        users = await self._read_json_file(self.users_file)
        
        if user_id in users:
            users[user_id]["last_login"] = datetime.now(timezone.utc).isoformat()
            await self._write_json_file(self.users_file, users)
    
    def _user_from_dict(self, user_data: Dict[str, Any]) -> User:
        """Convert dictionary to User model."""
        # Helper function to parse datetime with timezone awareness
        def parse_datetime(dt_str: str) -> datetime:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        
        return User(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=UserRole(user_data["role"]),
            is_active=user_data["is_active"],
            created_at=parse_datetime(user_data["created_at"]),
            updated_at=parse_datetime(user_data["updated_at"]),
            last_login=parse_datetime(user_data["last_login"]) if user_data["last_login"] else None,
            failed_login_attempts=user_data["failed_login_attempts"],
            locked_until=parse_datetime(user_data["locked_until"]) if user_data["locked_until"] else None,
        )
    
    # API Key management methods
    
    async def create_api_key(self, user_id: str, api_key_create: APIKeyCreate) -> APIKey:
        """Create a new API key."""
        api_keys = await self._read_json_file(self.api_keys_file)
        
        # Generate API key
        key = generate_api_key()
        key_hash = hash_api_key(key)
        
        key_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        api_key_data = {
            "id": key_id,
            "user_id": user_id,
            "name": api_key_create.name,
            "description": api_key_create.description,
            "permissions": [p.value for p in api_key_create.permissions],
            "key_hash": key_hash,
            "expires_at": api_key_create.expires_at.isoformat() if api_key_create.expires_at else None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_used": None,
            "usage_count": 0,
            "is_active": True,
        }
        
        api_keys[key_id] = api_key_data
        await self._write_json_file(self.api_keys_file, api_keys)
        
        api_key = self._api_key_from_dict(api_key_data)
        # Store the original key for return (only shown once)
        api_key._original_key = key
        
        return api_key
    
    async def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        api_keys = await self._read_json_file(self.api_keys_file)
        key_data = api_keys.get(key_id)
        
        if not key_data:
            return None
        
        return self._api_key_from_dict(key_data)
    
    async def list_user_api_keys(self, user_id: str) -> List[APIKey]:
        """List all API keys for a user."""
        api_keys = await self._read_json_file(self.api_keys_file)
        
        user_keys = [
            self._api_key_from_dict(key_data)
            for key_data in api_keys.values()
            if key_data["user_id"] == user_id
        ]
        
        user_keys.sort(key=lambda k: k.created_at)
        return user_keys
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke (deactivate) an API key."""
        api_keys = await self._read_json_file(self.api_keys_file)
        
        if key_id not in api_keys:
            return False
        
        api_keys[key_id]["is_active"] = False
        api_keys[key_id]["updated_at"] = datetime.utcnow().isoformat()
        
        await self._write_json_file(self.api_keys_file, api_keys)
        return True
    
    async def verify_api_key(self, key: str) -> Optional[APIKey]:
        """Verify an API key and return the associated key object."""
        key_hash = hash_api_key(key)
        api_keys = await self._read_json_file(self.api_keys_file)
        
        for key_data in api_keys.values():
            if (
                key_data["key_hash"] == key_hash
                and key_data["is_active"]
                and (
                    not key_data["expires_at"]
                    or datetime.now(timezone.utc) < datetime.fromisoformat(key_data["expires_at"])
                )
            ):
                # Update usage
                await self._update_api_key_usage(key_data["id"])
                return self._api_key_from_dict(key_data)
        
        return None
    
    async def _update_api_key_usage(self, key_id: str):
        """Update API key usage statistics."""
        api_keys = await self._read_json_file(self.api_keys_file)
        
        if key_id in api_keys:
            api_keys[key_id]["usage_count"] += 1
            api_keys[key_id]["last_used"] = datetime.now(timezone.utc).isoformat()
            await self._write_json_file(self.api_keys_file, api_keys)
    
    def _api_key_from_dict(self, key_data: Dict[str, Any]) -> APIKey:
        """Convert dictionary to APIKey model."""
        # Helper function to parse datetime with timezone awareness
        def parse_datetime(dt_str: str) -> datetime:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        
        return APIKey(
            id=key_data["id"],
            user_id=key_data["user_id"],
            name=key_data["name"],
            description=key_data["description"],
            permissions=[Permission(p) for p in key_data["permissions"]],
            key_hash=key_data["key_hash"],
            expires_at=parse_datetime(key_data["expires_at"]) if key_data["expires_at"] else None,
            created_at=parse_datetime(key_data["created_at"]),
            updated_at=parse_datetime(key_data["updated_at"]),
            last_used=parse_datetime(key_data["last_used"]) if key_data["last_used"] else None,
            usage_count=key_data["usage_count"],
            is_active=key_data["is_active"],
        )
    
    # Session management (for token blacklisting)
    
    async def blacklist_token(self, token_jti: str, expires_at: datetime):
        """Add token to blacklist."""
        sessions = await self._read_json_file(self.sessions_file)
        
        sessions[token_jti] = {
            "blacklisted_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        
        await self._write_json_file(self.sessions_file, sessions)
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted."""
        sessions = await self._read_json_file(self.sessions_file)
        return token_jti in sessions
    
    async def cleanup_expired_sessions(self):
        """Remove expired blacklisted tokens."""
        sessions = await self._read_json_file(self.sessions_file)
        now = datetime.now(timezone.utc)
        
        active_sessions = {
            jti: data
            for jti, data in sessions.items()
            if datetime.fromisoformat(data["expires_at"]) > now
        }
        
        await self._write_json_file(self.sessions_file, active_sessions)


# Global database instance
db = FileDatabase()