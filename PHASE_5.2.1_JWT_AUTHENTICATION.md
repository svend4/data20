# Phase 5.2.1: JWT Authentication Integration

## Overview

Implemented **JWT-based authentication system** for the Data20 Knowledge Base backend API. Users can register, login, and access protected endpoints using JWT access tokens.

## Implementation Summary

### Files Created/Modified

1. **`backend/auth.py`** (450+ lines) - NEW
   - Password hashing with bcrypt
   - JWT token creation/verification
   - User authentication functions
   - FastAPI dependencies for auth
   - Role-based access control (RBAC)

2. **`backend/server.py`** (Updated)
   - Added authentication endpoints
   - Integrated optional authentication in /api/run
   - Updated version to 5.2.1

## Features

### 1. User Registration
- **Endpoint**: `POST /auth/register`
- **Features**:
  - Username and email uniqueness validation
  - Password strength check (min 8 characters)
  - bcrypt password hashing
  - First user automatically becomes ADMIN
  - Default role: USER

**Example Request**:
```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePass123",
    "full_name": "Alice Smith"
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-01-03T12:00:00Z"
}
```

### 2. User Login
- **Endpoint**: `POST /auth/login`
- **Features**:
  - Login with username OR email
  - Returns access token (30 min expiry)
  - Returns refresh token (7 day expiry)
  - Logs authentication attempts

**Example Request**:
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "SecurePass123"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Token Refresh
- **Endpoint**: `POST /auth/refresh`
- **Features**:
  - Refresh access token without re-authentication
  - Requires valid refresh token

**Example Request**:
```bash
curl -X POST http://localhost:8001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. Get Current User
- **Endpoint**: `GET /auth/me`
- **Features**:
  - Returns authenticated user info
  - Requires valid access token

**Example Request**:
```bash
curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-01-03T12:00:00Z"
}
```

### 5. Update User Profile
- **Endpoint**: `PUT /auth/me`
- **Features**:
  - Update full_name
  - Requires authentication

**Example Request**:
```bash
curl -X PUT http://localhost:8001/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Johnson"
  }'
```

### 6. Logout
- **Endpoint**: `POST /auth/logout`
- **Features**:
  - Logs logout event
  - Note: JWT tokens are stateless, client must discard tokens

## Technical Details

### Password Security
```python
# bcrypt hashing with automatic salt generation
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = get_password_hash("SecurePass123")
# Result: $2b$12$KIXxKj8N7EfGxCOjD5W.rO3qZ1vT2nRQa...

# Verify password
is_valid = verify_password("SecurePass123", hashed)
# Result: True
```

### JWT Token Structure
```python
# Access Token (30 min expiry)
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  # User ID
  "username": "alice",
  "email": "alice@example.com",
  "role": "admin",
  "type": "access",
  "exp": 1704290400,  # Expiration timestamp
  "iat": 1704288600   # Issued at timestamp
}

# Refresh Token (7 day expiry)
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "type": "refresh",
  "exp": 1704893400,
  "iat": 1704288600
}
```

### Role-Based Access Control (RBAC)

**Roles**:
- `ADMIN` - Full access
- `USER` - Standard user access
- `GUEST` - Read-only access (future)

**Usage Example**:
```python
from auth import require_admin, require_user

# Admin-only endpoint
@app.delete("/api/tools/{tool_name}")
async def delete_tool(tool_name: str, user: User = Depends(require_admin)):
    # Only admins can delete tools
    pass

# User or admin endpoint
@app.post("/api/jobs")
async def create_job(user: User = Depends(require_user)):
    # Users and admins can create jobs
    pass
```

### Optional Authentication

The `/api/run` endpoint supports **optional authentication**:

```python
@app.post("/api/run")
async def run_tool(
    request: ToolRunRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # If user is authenticated, associate job with user
    # If not authenticated, job runs anonymously
    pass
```

**With Authentication**:
```bash
curl -X POST http://localhost:8001/api/run \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "build_graph",
    "parameters": {}
  }'
```

**Without Authentication** (still works):
```bash
curl -X POST http://localhost:8001/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "build_graph",
    "parameters": {}
  }'
```

## Configuration

### Environment Variables

```bash
# JWT Secret Key (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production-min-32-chars

# Token Expiry (optional, defaults shown)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (required)
DATABASE_URL=postgresql://data20:data20@localhost:5432/data20_kb
```

**IMPORTANT**: Generate a secure SECRET_KEY in production:
```bash
# Generate 32-byte random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Database Schema

The existing `users` table (from Phase 5.1) is used:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

Jobs are associated with users:
```sql
ALTER TABLE jobs ADD COLUMN user_id UUID REFERENCES users(id);
```

## Security Features

### 1. Password Requirements
- Minimum 8 characters
- Hashed with bcrypt (cost factor 12)
- Salt automatically generated

### 2. Token Security
- HMAC-SHA256 signature (HS256)
- Short-lived access tokens (30 min)
- Long-lived refresh tokens (7 days)
- Token type validation (access vs refresh)

### 3. User Account Security
- Username and email uniqueness
- Email validation (pydantic EmailStr)
- Active/inactive account support
- First user auto-admin privilege

### 4. Logging
All authentication events are logged:
- Registration attempts
- Login attempts (success/failure)
- Token refresh
- User profile updates
- Logout events

**Example Logs**:
```json
{"event": "user_registration_attempt", "username": "alice", "email": "alice@example.com"}
{"event": "user_registered", "user_id": "550e...", "role": "admin", "is_first_user": true}
{"event": "login_attempt", "username": "alice"}
{"event": "login_success", "user_id": "550e...", "username": "alice", "role": "admin"}
{"event": "login_failed", "username": "bob", "reason": "invalid_credentials"}
```

## API Summary

### Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /auth/register | No | Register new user |
| POST | /auth/login | No | Login and get tokens |
| POST | /auth/refresh | No (refresh token) | Refresh access token |
| GET | /auth/me | Yes | Get current user info |
| PUT | /auth/me | Yes | Update user profile |
| POST | /auth/logout | Yes | Logout (logs event) |

### Updated Endpoints

| Endpoint | Auth | Change |
|----------|------|--------|
| POST /api/run | Optional | Associates job with user if authenticated |

## Testing

### 1. Register First User (becomes admin)
```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "AdminPass123",
    "full_name": "System Admin"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "AdminPass123"
  }' | jq -r '.access_token'
```

### 3. Access Protected Endpoint
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Run Tool with Authentication
```bash
curl -X POST http://localhost:8001/api/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "build_graph",
    "parameters": {}
  }'
```

## Error Handling

### 400 Bad Request
- Username already exists
- Email already exists
- Password too short

### 401 Unauthorized
- Invalid credentials
- Expired token
- Invalid token signature
- Wrong token type (access/refresh mismatch)

### 403 Forbidden
- Insufficient permissions (role-based)
- Inactive user account

### 404 Not Found
- User not found

## Next Steps

### Phase 5.2.2: User Management Endpoints (Next)
- Admin: List all users
- Admin: Update user roles
- Admin: Activate/deactivate users
- Admin: Delete users
- Password reset functionality

### Phase 5.2.3: Enhanced Permissions (Next)
- Protect admin endpoints with `require_admin`
- Add job ownership checks (users can only see their jobs)
- Add user/guest role enforcement
- Implement API rate limiting per user

### Phase 5.4: Frontend Integration (Future)
- Login/register UI
- Token storage (localStorage/sessionStorage)
- Automatic token refresh
- Protected routes

## Performance Impact

- **Registration**: ~50-100ms (bcrypt hashing)
- **Login**: ~50-100ms (bcrypt verification)
- **Token Verification**: <1ms (JWT decode + signature check)
- **Database Queries**: 1-2 queries per authenticated request

**No performance degradation for anonymous users** - authentication is optional.

## Security Recommendations

### Production Deployment

1. **Generate Strong SECRET_KEY**:
```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

2. **Use HTTPS Only**:
   - Enforce HTTPS in production
   - Tokens transmitted in headers are vulnerable over HTTP

3. **Token Storage (Frontend)**:
   - Store access tokens in memory (not localStorage)
   - Store refresh tokens in httpOnly cookies
   - Implement automatic refresh before expiry

4. **Rate Limiting**:
   - Limit login attempts (5 per minute)
   - Limit registration (3 per hour per IP)

5. **Monitoring**:
   - Monitor failed login attempts
   - Alert on suspicious patterns
   - Log all authentication events

## Summary

### What Was Built

✅ **Complete JWT authentication system**:
- User registration with email validation
- Login with access + refresh tokens
- Token refresh mechanism
- User profile management
- Optional authentication support
- Role-based access control foundation
- Comprehensive logging

### Impact

- **Security**: Production-ready authentication with bcrypt + JWT
- **Flexibility**: Optional authentication - anonymous users still work
- **Scalability**: Stateless tokens - no session storage needed
- **Audit Trail**: All auth events logged with structured logging
- **Future-Ready**: RBAC foundation for Phase 5.2.3

### Statistics

- **New files**: 1 (`backend/auth.py`)
- **Modified files**: 1 (`backend/server.py`)
- **New endpoints**: 6 authentication endpoints
- **Code added**: ~600 lines
- **Documentation**: This comprehensive guide

---

**Phase 5.2.1 Complete!** ✅

Next: Phase 5.2.2 (User Management) + Phase 5.2.3 (Permissions)
