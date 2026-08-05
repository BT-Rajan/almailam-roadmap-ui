# Backend & Frontend Integration Guide

This guide covers the complete integration of the backend (Python/FastAPI) and frontend (Vue 3/TypeScript) with the authentication module.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Configuration](#configuration)
5. [Testing the Integration](#testing-the-integration)
6. [Security Considerations](#security-considerations)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Authentication Flow

```
User Login Form
       ↓
[Frontend] → POST /api/auth/login → [Backend]
       ↑                                    ↓
       ←── access_token + refresh_token ←──
       
API Requests
       ↓
[Frontend] → GET /api/resource (+ Bearer Token) → [Backend]
       ↑                                            ↓
       ←────────── Response ←──────────────────────
```

### Token Management

- **Access Token**: Short-lived JWT token (15 minutes default)
- **Refresh Token**: Long-lived token stored in database with rotation policy
- **Token Rotation**: Refresh tokens are rotated on every refresh for security
- **Auto-Refresh**: Client automatically refreshes tokens when access token expires

### Components Created

#### Backend Files
- `backend/scripts/create_admin_with_password.py` - Initialize admin user

#### Frontend Files
- `src/services/apiClient.ts` - HTTP client with token management
- `src/services/authService.ts` - Authentication API calls
- `src/stores/authStore.ts` - Pinia store for auth state
- `src/pages/LoginPage.vue` - Updated login page

#### Configuration
- `.env.example` - Environment variable template

---

## Backend Setup

### 1. Prerequisites

```bash
# Python 3.10+
python --version

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create database (MySQL)
mysql -u root -p -e "CREATE DATABASE almailam DEFAULT CHARSET=utf8mb4;"

# Import schema
mysql -u root -p almailam < schema.sql
```

### 3. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/almailam

# Security
SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Environment
ENV=development
DEBUG=true
```

### 4. Create Admin User

Run the admin creation script with the hardcoded password:

```bash
cd backend
python -m scripts.create_admin_with_password

# Output:
# [success] Created admin user 'admin' with email 'admin@serviceos.local'.
```

**Admin Credentials:**
- Username: `admin`
- Password: `Admin#99`
- Role: `Administrator`

### 5. Start the Backend Server

```bash
cd backend

# Using FastAPI/Uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Server will be available at: http://localhost:8000
# API Docs: http://localhost:8000/docs (in development)
```

---

## Frontend Setup

### 1. Prerequisites

```bash
# Node.js 18+
node --version
npm --version
```

### 2. Install Dependencies

```bash
cd frontend  # or root directory where package.json is
npm install
```

### 3. Environment Configuration

Create a `.env.local` file in the root directory:

```env
# API Base URL
VITE_API_URL=http://localhost:8000
```

Or copy from template:

```bash
cp .env.example .env.local
```

### 4. Start the Frontend Dev Server

```bash
npm run dev

# Frontend will be available at: http://localhost:5173
```

### 5. Build for Production

```bash
npm run build

# Output: dist/ directory ready for deployment
```

---

## Configuration

### API Client Configuration

The API client (`src/services/apiClient.ts`) handles:

- **Base URL**: Configurable via `VITE_API_URL` environment variable
- **Token Management**: Automatic Bearer token injection
- **Token Refresh**: Automatic 401 response handling with refresh
- **Error Handling**: Standardized error messages
- **Request Retries**: Automatic retry on token refresh

### Authentication Store

The auth store (`src/stores/authStore.ts`) provides:

```typescript
// State
isAuthenticated: boolean
accessToken: string | null
refreshToken: string | null
userInfo: UserInfo | null

// Getters
isAdmin: boolean
username: string
role: string

// Actions
login(username: string, password: string)
logout()
refreshTokens()
getCurrentUser()
changePassword(currentPassword, newPassword)
```

### Router Guards

Routes with `requiresAuth: true` metadata require authentication:

```typescript
{
  path: '/dashboard',
  name: 'dashboard',
  component: DashboardPage,
  meta: {
    requiresAuth: true,
    layout: 'dashboard'
  }
}
```

Unauthenticated users are redirected to `/login` with a redirect query parameter.

---

## Testing the Integration

### Manual Testing Workflow

#### 1. Test Login

```bash
# 1. Start both servers (backend on 8000, frontend on 5173)

# 2. Open http://localhost:5173 in browser
# 3. You should be redirected to login page

# 4. Enter credentials:
#    Username: admin
#    Password: Admin#99

# 5. Click "Sign In"
# 6. Should redirect to dashboard
```

#### 2. Test Token Refresh

```bash
# 1. Login successfully

# 2. Wait or manually test by opening browser DevTools
#    → Application/Storage → LocalStorage
#    → Verify tokens are stored:
#       - serviceos-access-token
#       - serviceos-refresh-token
#       - serviceos-user-info

# 3. Make an API request (e.g., navigate to Projects page)

# 4. Token should be automatically refreshed when expired
```

#### 3. Test Logout

```bash
# 1. Login successfully

# 2. Click logout button

# 3. Should redirect to login page

# 4. LocalStorage tokens should be cleared
```

#### 4. Test Protected Routes

```bash
# 1. Navigate directly to http://localhost:5173/dashboard
#    without logging in

# 2. Should redirect to login page with redirect query

# 3. Login with admin credentials

# 4. Should redirect back to /dashboard
```

### API Testing with cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin#99"}'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }

# Get Current User (using access token)
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

# Refresh Token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

---

## Security Considerations

### JWT Tokens

1. **Access Token**
   - Short expiration (15 minutes default)
   - Stored in memory (not localStorage)
   - Included in Authorization header

2. **Refresh Token**
   - Longer expiration (7 days default)
   - Stored in localStorage with `serviceos-refresh-token` key
   - Rotated on every refresh for security

3. **Token Rotation**
   - Old refresh token is revoked after use
   - Captured tokens can only be replayed once

### Password Security

1. **Hashing**
   - Passwords hashed using bcrypt in backend
   - Never transmitted or stored in plain text

2. **Admin Password**
   - Default admin password: `Admin#99`
   - **Should be changed immediately in production**
   - Change password: POST `/api/auth/change-password`

### CORS Configuration

Update CORS in backend based on your deployment:

```python
# backend/.env
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### Environment Variables

**Never commit secrets to version control:**

```bash
# .gitignore
.env
.env.local
.env.*.local
*.key
```

---

## Troubleshooting

### Common Issues

#### 1. CORS Error

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**:
```bash
# backend/.env
CORS_ORIGINS=http://localhost:5173
```
Then restart backend server.

#### 2. 401 Unauthorized

**Causes**:
- Token expired
- Invalid token
- User not active
- Session revoked

**Solution**:
- Clear browser cache/localStorage
- Delete `serviceos-*` keys from localStorage
- Login again

#### 3. Login Fails with "Invalid username or password"

**Check**:
```bash
# Verify admin user exists
mysql -u root -p almailam -e "SELECT id, username, role FROM users WHERE username='admin';"
```

**If not found**:
```bash
cd backend
python -m scripts.create_admin_with_password
```

#### 4. Token Refresh Loop

**Symptom**: Constant redirects to login

**Causes**:
- Invalid refresh token
- Database connection issue
- Refresh token expired

**Solution**:
1. Clear localStorage
2. Check backend database connection
3. Verify refresh tokens table: `SELECT * FROM refresh_tokens;`

#### 5. "Module not found" in Frontend

**Solution**:
```bash
cd frontend
npm install
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### 6. Backend Database Connection Error

**Check**:
```bash
# Verify MySQL is running
mysql -u root -p -e "SHOW DATABASES;"

# Verify almailam database exists
mysql -u root -p -e "USE almailam; SHOW TABLES;"

# Check .env DATABASE_URL format
# Should be: mysql+pymysql://user:password@host:3306/dbname
```

### Debug Mode

**Backend**:
```python
# backend/.env
DEBUG=true
```

Access API docs at `http://localhost:8000/docs`

**Frontend**:
```bash
# In browser DevTools → Console
localStorage.getItem('serviceos-access-token')
localStorage.getItem('serviceos-user-info')
```

---

## Next Steps

1. **Create Additional Users**: Modify `create_admin_with_password.py` or create a user management endpoint
2. **Password Reset**: Implement email-based password reset flow
3. **Two-Factor Authentication**: Add 2FA for enhanced security
4. **Role-Based Access Control**: Implement permissions checking in routes
5. **Audit Logging**: Track user actions via audit_log table
6. **API Documentation**: Update OpenAPI docs for all endpoints

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend logs: `tail -f backend/logs/app.log`
3. Check browser console for frontend errors
4. Verify all services are running:
   - Backend: `curl http://localhost:8000/api/health`
   - Frontend: `curl http://localhost:5173` (should return HTML)

