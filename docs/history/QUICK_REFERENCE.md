# 🎯 ServiceOS Development Quick Reference

## 🚀 Quick Start (Copy-Paste)

```bash
# Terminal 1: Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Setup database (MySQL must be running)
mysql -u root -p -e "CREATE DATABASE almailam DEFAULT CHARSET=utf8mb4;"
mysql -u root -p almailam < schema.sql

# Create admin user
python -m scripts.create_admin --quick-start

# Start server
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
npm install
npm run dev
```

**Result**: Frontend at http://localhost:5173, Backend at http://localhost:8000

---

## 🔐 Default Credentials

```
Username: admin
Password: Admin#99
```

> ⚠️ **Change this in production!**

---

## 📡 API Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/auth/login` | Login | ❌ |
| POST | `/api/auth/refresh` | Refresh token | ❌ |
| POST | `/api/auth/logout` | Logout | ✅ |
| GET | `/api/auth/me` | Current user | ✅ |
| GET | `/api/health` | Health check | ❌ |

---

## 🔑 Common Commands

### Backend

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create admin user (interactive)
python -m scripts.create_admin

# Create admin with specific password
python -m scripts.create_admin --password "YourPassword#123"

# Create admin with quick-start password
python -m scripts.create_admin --quick-start

# Start server
python -m uvicorn app.main:app --reload

# Start server on different port
python -m uvicorn app.main:app --reload --port 8001

# Database management
mysql -u root -p almailam < schema.sql  # Import schema
mysql -u root -p almailam               # Connect to database
```

### Frontend

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter/formatter
npm run lint
```

---

## 📝 Frontend Components

### Login Page
**File**: `src/pages/LoginPage.vue`
```vue
<script setup>
const { isSubmitting } = useAuth()
// Auto handles login via authStore
</script>
```

### Use Auth in Components
```vue
<script setup lang="ts">
import { useAuth } from '@/composables/useAuthComposable'

const { isAuthenticated, user, login, logout } = useAuth()
</script>

<template>
  <div v-if="isAuthenticated">
    Welcome {{ user?.name }}!
    <button @click="logout">Logout</button>
  </div>
</template>
```

### Make API Calls
```typescript
import { apiClient } from '@/services/httpClient'

// Automatically includes Authorization header
const data = await apiClient.get('/api/projects')

// POST with body
const result = await apiClient.post('/api/projects', {
  name: 'New Project',
  description: 'Description'
})
```

---

## 🗄️ Database

### Key Tables

```sql
-- Users
SELECT id, username, email, role, is_active FROM users;

-- Refresh Tokens
SELECT jti, user_id, revoked, expires_at FROM refresh_tokens;

-- Check admin user
SELECT * FROM users WHERE username='admin' AND role='Administrator';

-- Cleanup expired tokens
DELETE FROM refresh_tokens WHERE expires_at < NOW();
```

---

## 🔧 Configuration

### Frontend (.env.local)
```env
# Optional - use Vite proxy by default
VITE_API_BASE_URL=http://localhost:8000
```

### Backend (.env)
```env
ENV=development
DEBUG=true
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=almailam
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
```

---

## 🐛 Troubleshooting

### Can't connect to backend
```bash
# Check if server is running
curl http://localhost:8000/api/health

# Check if port is available
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Can't login
```bash
# Verify admin user exists
mysql -u root -p almailam -e "SELECT * FROM users WHERE username='admin';"

# Recreate if needed
python -m scripts.create_admin --quick-start

# Test with cURL
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin#99"}'
```

### Can't connect to database
```bash
# Start MySQL service
# macOS: brew services start mysql
# Linux: sudo systemctl start mysql
# Windows: net start MySQL80

# Create database if missing
mysql -u root -p -e "CREATE DATABASE almailam DEFAULT CHARSET=utf8mb4;"

# Import schema
mysql -u root -p almailam < schema.sql
```

### Port already in use
```bash
# Find and kill process using port
# macOS/Linux:
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Use different port:
python -m uvicorn app.main:app --port 8001
```

---

## 🧪 Testing with cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin#99"}'

# Save token (replace with actual token)
export TOKEN="eyJ0eXAiOiJKV1Q..."

# Get current user
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Health check
curl http://localhost:8000/api/health
```

---

## 📦 Project Structure

```
almailam-roadmap-ui/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── services/     # Business logic
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── core/         # Config, security, database
│   ├── scripts/
│   │   └── create_admin.py
│   ├── schema.sql        # Database schema
│   └── requirements.txt   # Python dependencies
│
├── src/                  # Vue 3 frontend
│   ├── components/       # Vue components
│   ├── composables/      # Vue composables (like useAuth)
│   ├── services/         # API services
│   ├── stores/          # Pinia stores (state management)
│   ├── pages/           # Page components
│   ├── router/          # Vue Router configuration
│   ├── utils/           # Utilities
│   └── types/           # TypeScript types
│
├── package.json          # Frontend dependencies
├── vite.config.ts        # Frontend build config
└── .env.example          # Environment template
```

---

## 🔐 Security Checklist

- [ ] Change admin password from `Admin#99`
- [ ] Set `DEBUG=false` in production
- [ ] Generate strong `JWT_SECRET_KEY`
- [ ] Use HTTPS in production
- [ ] Update `CORS_ORIGINS` for production domain
- [ ] Set `ENV=production` in backend
- [ ] Back up database regularly
- [ ] Set up monitoring/logging
- [ ] Keep dependencies updated

---

## 📚 Useful Links

| Resource | URL |
|----------|-----|
| FastAPI Docs | https://fastapi.tiangolo.com |
| Vue 3 Guide | https://vuejs.org |
| Pinia | https://pinia.vuejs.org |
| JWT.io | https://jwt.io |
| MySQL Docs | https://dev.mysql.com |
| Vite | https://vitejs.dev |
| TypeScript | https://www.typescriptlang.org |

---

## 💡 Tips

- **Frontend debugging**: `console.log(JSON.parse(localStorage.getItem('almailam-refresh-token')))`
- **API debugging**: Add `?skip_auth=true` to bypass auth in development
- **Database reset**: `mysql -u root -p almailam -e "DROP TABLE *; "`
- **Hot reload**: Frontend and backend both support hot reload - changes apply instantly
- **API testing**: Use VS Code REST Client extension for easy API testing

---

## 🎓 Learning Path

1. **Understand the flow**: Read `FINAL_SUMMARY.md`
2. **Set up locally**: Follow Quick Start above
3. **Test the API**: Use cURL commands
4. **Explore code**: Check `src/services/authService.ts`
5. **Modify**: Try changing login form or adding new routes
6. **Deploy**: Follow `COMPLETE_SETUP_GUIDE.md` for production

---

**Keep this handy while developing!** 📌

Last Updated: August 2024 | Version: 1.0
