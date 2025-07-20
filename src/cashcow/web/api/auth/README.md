# CashCow Authentication System

This document describes the JWT-based authentication system implemented for the CashCow web API.

## Overview

The authentication system provides:

- **JWT Token Authentication**: Secure stateless authentication using JWT tokens
- **API Key Authentication**: Long-lived API keys for external integrations
- **Role-Based Access Control (RBAC)**: Admin, User, and ReadOnly roles
- **Permission-Based Authorization**: Fine-grained permissions for different operations
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Security Headers**: Comprehensive security headers and CORS protection
- **File-Based Storage**: Simple JSON file storage for users and API keys (no external database required)

## Quick Start

### 1. Installation

The authentication dependencies are automatically installed with the project:

```bash
poetry install
```

### 2. Default Admin User

A default admin user is created automatically:

- **Email**: `admin@cashcow.dev`
- **Password**: `changeme`
- **Role**: `admin`

### 3. Login

```bash
# Login to get JWT tokens
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@cashcow.dev",
       "password": "changeme"
     }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4. Using Authentication

Include the JWT token in the Authorization header:

```bash
curl -X GET "http://localhost :8001/api/users/me" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Or use an API key:

```bash
curl -X GET "http://localhost :8001/api/entities" \
     -H "X-API-Key: YOUR_API_KEY"
```

## API Endpoints

### Authentication Endpoints

- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/logout` - Logout (token invalidation)
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/status` - Auth system status

### User Management Endpoints (Admin Only)

- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `GET /api/users/{user_id}` - Get user details
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user
- `POST /api/users/{user_id}/activate` - Activate user
- `POST /api/users/{user_id}/deactivate` - Deactivate user

### API Key Management

- `GET /api/api-keys` - List your API keys
- `POST /api/api-keys` - Create new API key
- `GET /api/api-keys/{key_id}` - Get API key details
- `DELETE /api/api-keys/{key_id}` - Revoke API key
- `GET /api/api-keys/{key_id}/usage` - Get usage stats

## Roles and Permissions

### Roles

1. **Admin**: Full system access
2. **User**: Standard user access (own entities, reports, calculations)
3. **ReadOnly**: Read-only access to entities and reports

### Permissions

- `READ_ENTITIES` - View entities
- `WRITE_ENTITIES` - Create/update entities
- `DELETE_ENTITIES` - Delete entities
- `READ_USERS` - View user list (admin)
- `WRITE_USERS` - Create/update users (admin)
- `DELETE_USERS` - Delete users (admin)
- `ADMIN_ACCESS` - Administrative functions
- `API_KEY_MANAGE` - Manage API keys
- `READ_REPORTS` - View reports
- `GENERATE_REPORTS` - Generate reports
- `RUN_CALCULATIONS` - Run financial calculations

## Protecting Existing Endpoints

The authentication system integrates seamlessly with existing endpoints. Here's how to protect them:

### Basic Authentication

```python
from fastapi import Depends
from .auth import get_current_user, TokenData

@router.get("/entities")
async def list_entities(
    current_user: TokenData = Depends(get_current_user),
):
    # User is now authenticated
    # Access user info via current_user.user_id, current_user.role, etc.
    pass
```

### Permission-Based Protection

```python
from .auth import require_permission, Permission

@router.post("/entities")
async def create_entity(
    entity_data: dict,
    current_user: TokenData = Depends(require_permission(Permission.WRITE_ENTITIES)),
):
    # User has WRITE_ENTITIES permission
    pass
```

### Role-Based Protection

```python
from .auth import require_admin

@router.get("/admin/stats")
async def get_admin_stats(
    current_user: TokenData = Depends(require_admin()),
):
    # Only admins can access this endpoint
    pass
```

### Using Dependencies

The dependencies module provides convenient functions:

```python
from ..dependencies import require_entity_read, require_entity_write

@router.get("/entities")
async def list_entities(
    current_user: TokenData = Depends(require_entity_read()),
):
    pass

@router.post("/entities")
async def create_entity(
    current_user: TokenData = Depends(require_entity_write()),
):
    pass
```

## Security Features

### Rate Limiting

- 100 requests per minute per IP by default
- Configurable in middleware
- Returns HTTP 429 when exceeded

### Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`
- And more...

### Password Security

- Minimum 8 characters
- Must contain 3 of: uppercase, lowercase, numbers, special characters
- Bcrypt hashing with salt

### Token Security

- JWT tokens with configurable expiration (30 minutes default)
- Refresh tokens (7 days default)
- Secure secret key (configurable)

### API Key Security

- 32-character random keys
- SHA-256 hashing for storage
- Per-key permissions
- Usage tracking
- Optional expiration

## Configuration

### Environment Variables

Set these environment variables to customize the authentication system:

```bash
# Security
CASHCOW_SECRET_KEY=your-very-secure-secret-key-change-this
CASHCOW_ACCESS_TOKEN_EXPIRE_MINUTES=30
CASHCOW_REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
CASHCOW_RATE_LIMIT_REQUESTS=100
CASHCOW_RATE_LIMIT_WINDOW_MINUTES=15

# Data Directory
CASHCOW_AUTH_DATA_DIR=./data/auth
```

### File Storage

Authentication data is stored in JSON files:

```
data/auth/
├── users.json          # User accounts
├── api_keys.json       # API keys
├── sessions.json       # Blacklisted tokens
└── login_attempts.json # Login attempt logs
```

## Development and Testing

### Creating Test Users

```python
from cashcow.web.api.auth import db
from cashcow.web.api.auth.models import UserCreate, UserRole

# Create a test user
user = await db.create_user(UserCreate(
    email="test@example.com",
    full_name="Test User",
    password="testpass123",
    role=UserRole.USER
))
```

### Testing Authentication

```python
import pytest
from httpx import AsyncClient

async def test_login(client: AsyncClient):
    response = await client.post("/api/auth/login", json={
        "email": "admin@cashcow.dev",
        "password": "changeme"
    })
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
```

### Debugging

Enable debug logging to see authentication flow:

```python
import logging
logging.getLogger("cashcow.web.api.auth").setLevel(logging.DEBUG)
```

## Security Considerations

1. **Change Default Credentials**: Change the default admin password immediately
2. **Use HTTPS**: Always use HTTPS in production
3. **Secure Secret Key**: Use a strong, random secret key
4. **Token Rotation**: Implement token rotation for enhanced security
5. **Rate Limiting**: Monitor and adjust rate limits based on usage
6. **API Key Management**: Regularly rotate API keys
7. **Audit Logging**: Monitor login attempts and failed authentications

## Production Deployment

For production deployment:

1. Set secure environment variables
2. Use a proper secret management system
3. Consider using a database instead of JSON files for better performance
4. Implement proper logging and monitoring
5. Set up backup procedures for authentication data
6. Configure proper CORS origins
7. Use a reverse proxy with SSL termination

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check token format and expiration
2. **403 Forbidden**: User lacks required permissions
3. **429 Too Many Requests**: Rate limit exceeded
4. **Invalid credentials**: Check email/password combination

### Log Analysis

Check logs for authentication issues:

```bash
# View authentication logs
grep "auth" /path/to/logs/cashcow.log

# View failed login attempts
grep "auth_failed" /path/to/logs/cashcow.log
```

## Future Enhancements

Planned improvements:

1. **Database Integration**: PostgreSQL/MySQL support
2. **OAuth2 Integration**: Google, GitHub, etc.
3. **Multi-Factor Authentication**: TOTP support
4. **Session Management**: Advanced session controls
5. **Audit Logging**: Comprehensive audit trails
6. **SSO Integration**: SAML/LDAP support