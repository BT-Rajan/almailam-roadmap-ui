# ServiceOS - Complete Backend & Frontend Integration Guide

**Status**: ✅ Production-Ready with Admin Authentication

This guide covers complete setup, testing, and deployment of ServiceOS with integrated backend and frontend, focusing on the authentication module with default admin credentials `admin` / `Admin#99`.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Requirements](#system-requirements)
3. [Local Development Setup](#local-development-setup)
4. [Testing & Verification](#testing--verification)
5. [Production Deployment](#production-deployment)
6. [Security Best Practices](#security-best-practices)
7. [Troubleshooting](#troubleshooting)
8. [API Documentation](#api-documentation)

---

## Architecture Overview

### Technology Stack

**Backend**:
- Framework: FastAPI (Python 3.10+)
- Database: MySQL 8.0+
- Authentication: JWT (HS256)
- Token Management: Access + Refresh tokens with rotation

**Frontend**:
- Framework: Vue 3 with TypeScript
- State Management: Pinia
- Build Tool: Vite
- Styling: Tailwind CSS

### Authentication Flow

```
User Browser                    Frontend (Vue)              Backend (FastAPI)        Database
     │                              │                            │                      │
     ├─ Login Form ────────────────>│                            │                      │
     │                              │                            │                      │
     │                              ├─ POST /api/auth/login ────>│                      │
     │                              │                            ├─ Query User ────────>│
     │                              │                            │<────── User ────────│
     │                              │                            │ (hash password)      │
     │                              │<─ {access, refresh token} ─│                      │
     │                              │ (create RefreshToken rec)   │                      │
     │                              │                            ├─ Store in DB ──────>│
     │                              │<────────────────────────────┤                      │
     │<────── Store in localStorage ┤                            │                      │
     │         (tokens + user info) │                            │                      │
     │                              │                            │                      │
     ├─ Navigate to Dashboard ──────>│                            │                      │
     │                              ├─ GET /api/resources ──────>│                      │
     │                              │  (+Authorization header)    │ (verify JWT)         │
     │                              │<──── Resource Data ────────│                      │
     │                              │                            │                      │
```

### Session Management

- **Session Storage**: JWT tokens + refresh token in browser localStorage
- **Token Lifetime**: 
  - Access Token: 15 minutes (short-lived)
  - Refresh Token: 7 days (long-lived, stored in database)
- **Token Refresh**: Automatic on API request with expired access token
- **Token Rotation**: Old refresh token revoked after successful refresh
- **Logout**: Refresh token revoked in database

---

## System Requirements

### Backend
- Python 3.10 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### Frontend
- Node.js 18 or higher
- npm 9 or higher

### Development Machine
- 4GB RAM minimum
- 500MB free disk space
- Git (for cloning the repository)

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/BT-Rajan/almailam-roadmap-ui.git
cd almailam-roadmap-ui
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 2.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your database credentials
# Minimal config for development:
# ENV=development
# DEBUG=true
# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=
# DB_NAME=almailam
```

#### 2.4 Set Up Database

```bash
# Create the database
mysql -u root -p -e "CREATE DATABASE almailam DEFAULT CHARSET=utf8mb4;"

# Import the schema
mysql -u root -p almailam < schema.sql

# Verify tables were created
mysql -u root -p almailam -e "SHOW TABLES;"
```

#### 2.5 Create Admin User

**Option A: Quick-Start (Development)**
```bash
# Uses default password: Admin#99
python -m scripts.create_admin --quick-start

# Output:
# [info] Using quick-start password: 'Admin#99' (development only).
# [ok] Created admin user 'admin' with role 'Administrator'.
# [warn] ⚠️ This is a development password. Change it in production!
```

**Option B: Custom Password**
```bash
# You'll be prompted for password securely
python -m scripts.create_admin

# Or non-interactively
python -m scripts.create_admin --password "YourSecurePassword#123"
```

#### 2.6 Start Backend Server

```bash
# Make sure you're in the backend directory with venv activated
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Application startup complete
```

**Verify Backend**:
```bash
# In another terminal
curl http://localhost:8000/api/health

# Expected response:
# {"status":"ok","env":"development"}
```

### Step 3: Frontend Setup

#### 3.1 Install Dependencies

```bash
# Go to frontend directory (root of the repo)
cd ..  # Go back to project root
npm install
```

#### 3.2 Configure Environment Variables

```bash
# Copy the example (frontend uses Vite proxy by default)
cp .env.example .env.local

# For development with default Vite proxy, file can be empty
# For pointing to different backend:
# VITE_API_BASE_URL=http://localhost:8000
```

#### 3.3 Start Development Server

```bash
npm run dev

# Expected output:
# VITE v6.0.11  ready in 145 ms
# ➜  Local:   http://localhost:5173/
# ➜  press h to show help
```

### Step 4: Test the Integration

1. **Open Frontend**: http://localhost:5173 in your browser
2. **You'll be redirected** to: http://localhost:5173/login
3. **Enter credentials**:
   - Username: `admin`
   - Password: `Admin#99`
4. **Click "Sign In"**
5. **Expected result**: Redirect to Dashboard

---

## Testing & Verification

### Browser DevTools Inspection

**Verify Tokens are Stored**:

1. Open Browser DevTools (F12)
2. Go to: Application → Storage → Local Storage → http://localhost:5173
3. You should see:
   - `almailam-refresh-token`: (long JWT string)
   - Note: `accessToken` is stored in memory, not localStorage (for security)

### API Testing with cURL

```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin#99"}'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }

# Save the tokens
export ACCESS_TOKEN="<access_token_from_response>"
export REFRESH_TOKEN="<refresh_token_from_response>"

# 2. Get Current User (requires access token)
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Response:
# {
#   "id": "1",
#   "name": "Administrator",
#   "designation": null,
#   "email": "admin@example.com",
#   "mobile": null,
#   "role": "Administrator",
#   "avatar": "...",
#   "status": "active"
# }

# 3. Refresh Token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"

# 4. Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"
```

### Test Scenarios

**✅ Test 1: Successful Login**
- Navigate to http://localhost:5173
- Enter `admin` / `Admin#99`
- Should see dashboard

**✅ Test 2: Invalid Credentials**
- Navigate to http://localhost:5173
- Enter `admin` / `wrongpassword`
- Should see error message

**✅ Test 3: Protected Routes**
- Without login, go directly to http://localhost:5173/projects
- Should redirect to login

**✅ Test 4: Token Refresh**
- Login successfully
- Open DevTools → Network tab
- Navigate to any page
- Wait for access token expiration (15 minutes)
- Make an API request
- Should see automatic token refresh request

**✅ Test 5: Session Persistence**
- Login and note the tokens in localStorage
- Close browser completely
- Reopen http://localhost:5173
- Should automatically restore session (no login prompt)

**✅ Test 6: Logout**
- Login successfully
- Click logout
- Should redirect to login
- localStorage should be cleared

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Change admin password from `Admin#99`
- [ ] Set `DEBUG=false` in backend `.env`
- [ ] Set `ENV=production` in backend `.env`
- [ ] Generate strong `JWT_SECRET_KEY`
- [ ] Configure production database (managed database service recommended)
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure production `CORS_ORIGINS`
- [ ] Set up monitoring and logging
- [ ] Back up database regularly
- [ ] Run security audit

### Backend Deployment

#### Option 1: Docker Deployment

**Create Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app
COPY scripts/ ./scripts

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run**:
```bash
docker build -t serviceos-backend .
docker run -p 8000:8000 --env-file .env serviceos-backend
```

#### Option 2: Cloud Deployment (AWS EC2)

```bash
# 1. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip mysql-client

# 3. Clone repository
git clone <your-repo> /opt/serviceos
cd /opt/serviceos/backend

# 4. Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with production values

# 6. Set up systemd service
sudo tee /etc/systemd/system/serviceos.service > /dev/null <<EOF
[Unit]
Description=ServiceOS API
After=network.target mysql.service

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/serviceos/backend
ExecStart=/opt/serviceos/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable serviceos
sudo systemctl start serviceos

# 8. Check status
sudo systemctl status serviceos
```

### Frontend Deployment

#### Option 1: Static Hosting (Netlify, Vercel)

```bash
# Build for production
npm run build

# Output is in dist/ directory
# Deploy the entire dist/ directory to your hosting service

# For Netlify:
# npm install -g netlify-cli
# netlify deploy --prod --dir=dist

# Important: Set build environment variable
# VITE_API_BASE_URL=https://api.yourdomain.com
```

#### Option 2: Docker Deployment

**Create Dockerfile** (root `Dockerfile`):
```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM node:18-alpine

WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

**Build and Run**:
```bash
docker build -t serviceos-frontend .
docker run -p 3000:3000 -e VITE_API_BASE_URL=https://api.yourdomain.com serviceos-frontend
```

#### Option 3: Traditional Web Server (Nginx)

**Nginx Configuration** (`/etc/nginx/sites-available/serviceos`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Root directory with built Vue app
    root /var/www/serviceos/dist;
    index index.html;
    
    # Vue router: route all non-file requests to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

**Deploy**:
```bash
# 1. Build frontend
npm run build

# 2. Copy to web server
sudo mkdir -p /var/www/serviceos
sudo cp -r dist/* /var/www/serviceos/dist/

# 3. Enable Nginx config
sudo ln -s /etc/nginx/sites-available/serviceos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Security Best Practices

### 1. Change Default Admin Password Immediately

```bash
# Login to frontend with admin / Admin#99
# Go to Settings/Profile
# Change password to a strong password (min 8 chars, mix of letters/numbers/symbols)
```

### 2. Environment Variables

**Never commit `.env` files**:
```bash
# .gitignore
.env
.env.local
.env.*.local
```

**Use strong secrets**:
```bash
# Generate JWT secret
openssl rand -hex 32

# Use for JWT_SECRET_KEY in production
```

### 3. CORS Configuration

**Only allow trusted origins**:
```bash
# Production .env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# NOT: *  (never use wildcard in production)
```

### 4. HTTPS/SSL

**Always use HTTPS in production**:
```bash
# Get free SSL certificates from Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com
```

### 5. Database Security

**Strong database credentials**:
```bash
# Create dedicated database user (not root)
CREATE USER 'serviceos'@'localhost' IDENTIFIED BY 'StrongPassword#123!';
GRANT ALL PRIVILEGES ON almailam.* TO 'serviceos'@'localhost';
FLUSH PRIVILEGES;

# Use in backend .env
DB_USER=serviceos
DB_PASSWORD=StrongPassword#123!
```

### 6. API Rate Limiting

**Implement rate limiting** (add to backend):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(...):
    # Max 5 login attempts per minute per IP
```

### 7. Regular Updates

```bash
# Keep dependencies updated
pip list --outdated
npm outdated

# Update with caution
pip install --upgrade package-name
npm update package-name
```

---

## Troubleshooting

### Frontend Issues

**Issue: "Cannot reach backend" / CORS errors**

Solution:
```bash
# 1. Verify backend is running
curl http://localhost:8000/api/health

# 2. Check Vite proxy configuration (vite.config.ts)
# Should have: /api proxy to http://localhost:8000

# 3. Check browser console for specific error
# Dev Tools → Console

# 4. In production, update CORS_ORIGINS in backend .env
CORS_ORIGINS=https://yourdomain.com
# Restart backend
```

**Issue: "Cannot login" / 401 Unauthorized**

Solution:
```bash
# 1. Verify admin user exists
mysql -u root -p almailam -e "SELECT username, role FROM users WHERE username='admin';"

# 2. Verify password with cURL
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin#99"}'

# 3. If user doesn't exist, recreate:
cd backend && python -m scripts.create_admin --quick-start
```

**Issue: Tokens not persisting**

Solution:
```bash
# 1. Check localStorage in DevTools
# DevTools → Application → Local Storage → http://localhost:5173
# Should see: almailam-refresh-token

# 2. Verify browser allows localStorage
# Check privacy settings

# 3. Check browser console for errors
# DevTools → Console

# 4. Clear cache and try again
# Ctrl+Shift+Delete → Clear cache
```

### Backend Issues

**Issue: Database connection failed**

Solution:
```bash
# 1. Verify MySQL is running
mysql -u root -p -e "SELECT 1;"

# 2. Verify database exists
mysql -u root -p -e "SHOW DATABASES;" | grep almailam

# 3. Check .env database URL format
# Should be: mysql+pymysql://user:password@host:port/database

# 4. Test connection
python -c "
from app.core.database import SessionLocal
db = SessionLocal()
print('Connection successful!')
db.close()
"
```

**Issue: Server won't start / Port already in use**

Solution:
```bash
# 1. Check what's using port 8000
lsof -i :8000  # On macOS/Linux
netstat -ano | findstr :8000  # On Windows

# 2. Kill the process
kill -9 <PID>  # On macOS/Linux
taskkill /PID <PID> /F  # On Windows

# 3. Use different port
uvicorn app.main:app --port 8001

# 4. Or set in vite.config.ts for frontend
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
    },
  },
}
```

**Issue: Import errors / Module not found**

Solution:
```bash
# 1. Verify Python version
python --version  # Should be 3.10+

# 2. Verify virtual environment is active
# Should see (venv) in terminal prompt

# 3. Reinstall requirements
pip install -r requirements.txt --force-reinstall

# 4. Check Python path
which python  # Should point to venv
```

---

## API Documentation

### Authentication Endpoints

#### POST /api/auth/login

Login and get access + refresh tokens.

**Request**:
```json
{
  "username": "admin",
  "password": "Admin#99"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors**:
- 400: Invalid credentials
- 423: Account locked (too many failed attempts)

---

#### GET /api/auth/me

Get current authenticated user information.

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": "1",
  "name": "Administrator",
  "email": "admin@example.com",
  "mobile": null,
  "role": "Administrator",
  "designation": null,
  "avatar": "...",
  "status": "active"
}
```

**Errors**:
- 401: Unauthorized (invalid or missing token)

---

#### POST /api/auth/refresh

Refresh access token using refresh token.

**Request**:
```json
{
  "refresh_token": "<refresh_token>"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors**:
- 401: Invalid or expired refresh token

---

#### POST /api/auth/logout

Logout and revoke refresh token.

**Request**:
```json
{
  "refresh_token": "<refresh_token>"
}
```

**Response** (200 OK):
```json
{
  "message": "Logged out."
}
```

---

## Support & Next Steps

### Common Next Steps

1. **User Management**: Create additional users for different roles
2. **Password Reset**: Implement email-based password reset
3. **Two-Factor Authentication**: Add 2FA for enhanced security
4. **Role-Based Access Control**: Implement permission checks
5. **Audit Logging**: Track user actions
6. **Monitoring**: Set up error tracking and performance monitoring

### Getting Help

1. Check the troubleshooting section above
2. Review backend logs: `tail -f backend/logs/app.log`
3. Check browser console (DevTools → Console)
4. Verify all services are running:
   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:5173
   ```

### Documentation Links

- FastAPI: https://fastapi.tiangolo.com
- Vue 3: https://vuejs.org
- Pinia: https://pinia.vuejs.org
- MySQL: https://dev.mysql.com
- JWT: https://jwt.io

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready ✅
