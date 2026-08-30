#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS - Test Instance Setup
#
# Self-running, non-interactive setup for a fresh test instance:
#   - connects only as app_user (no root DB access on this server)
#   - creates database "alhadi-test" if it doesn't exist yet
#   - loads schema.sql only (no test/demo data)
#   - creates the admin login (admin / Admin#99) and nothing else
#   - opens firewall ports 8888 (backend) and 9007 (frontend) via ufw
#   - runs backend (8888) and frontend dev server (9007) as separate processes
#
# Run once on a fresh box:
#   ./test.sh
#
# Re-running is safe: schema load is idempotent (CREATE TABLE IF NOT
# EXISTS), the admin script skips if the user already exists, and both
# server processes are restarted.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"

BACKEND_PID_FILE="$SCRIPT_DIR/test-backend.pid"
BACKEND_LOG_FILE="$SCRIPT_DIR/test-backend.log"
FRONTEND_PID_FILE="$SCRIPT_DIR/test-frontend.pid"
FRONTEND_LOG_FILE="$SCRIPT_DIR/test-frontend.log"

DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="alhadi-test"
DB_USER="app_user"
DB_PASSWORD="Chennai#44"

BACKEND_PORT="8888"
FRONTEND_PORT="9007"

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$1"; }
die()  { printf '\033[1;31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }

# ----------------------------------------------------------------------------
# 1. Requirements
# ----------------------------------------------------------------------------

log "Checking requirements"

for cmd in python3 node npm curl openssl; do
    command -v "$cmd" >/dev/null 2>&1 || die "Missing required command: $cmd"
done

DB_CLIENT=""
command -v mariadb >/dev/null 2>&1 && DB_CLIENT=mariadb
[[ -z "$DB_CLIENT" ]] && command -v mysql >/dev/null 2>&1 && DB_CLIENT=mysql
[[ -z "$DB_CLIENT" ]] && die "Neither 'mariadb' nor 'mysql' client found. Install MariaDB/MySQL first."

APP_CLIENT=(--protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER")

# ----------------------------------------------------------------------------
# 2. Database (connect as app_user only -- no root access on this server)
# ----------------------------------------------------------------------------

log "Connecting as ${DB_USER}"

MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" "${APP_CLIENT[@]}" -e "SELECT 1;" >/dev/null 2>&1 ||
    die "Cannot connect as ${DB_USER}/${DB_PASSWORD}. Confirm this user exists and can log in from localhost."

log "Creating database '$DB_NAME' if needed"

if ! MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" "${APP_CLIENT[@]}" -e "USE \`${DB_NAME}\`;" >/dev/null 2>&1; then
    MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" "${APP_CLIENT[@]}" -e "
        CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci;
    " || die "Could not create database '${DB_NAME}' as ${DB_USER} -- ask an admin to create it and GRANT ALL on it to ${DB_USER}, or create it manually and re-run."
fi

unset MYSQL_PWD

# ----------------------------------------------------------------------------
# 3. Schema (fresh instance -> load schema.sql only, no test data)
# ----------------------------------------------------------------------------

log "Loading schema into '$DB_NAME'"

MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" "${APP_CLIENT[@]}" "$DB_NAME" < "$BACKEND_DIR/schema.sql"
unset MYSQL_PWD

# ----------------------------------------------------------------------------
# 4. backend/.env
# ----------------------------------------------------------------------------

log "Writing backend/.env"

JWT_SECRET="$(openssl rand -hex 32)"

cat > "$ENV_FILE" <<EOF
ENV=development
DEBUG=true

HOST=0.0.0.0
PORT=${BACKEND_PORT}

DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

CORS_ORIGINS=http://localhost:${FRONTEND_PORT},http://localhost:${BACKEND_PORT}

JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

MAX_LOGIN_ATTEMPTS=5
LOCKOUT_MINUTES=15
EOF

# ----------------------------------------------------------------------------
# 5. Python backend
# ----------------------------------------------------------------------------

log "Setting up Python backend"

cd "$BACKEND_DIR"

[[ -d venv ]] || python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate

python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q

# ----------------------------------------------------------------------------
# 6. Admin login only -- no test/demo data
# ----------------------------------------------------------------------------

log "Creating admin login (admin / Admin#99)"

python -m scripts.create_admin --quick-start

deactivate
cd "$SCRIPT_DIR"

# ----------------------------------------------------------------------------
# 7. Frontend deps
# ----------------------------------------------------------------------------

log "Installing frontend dependencies"

npm install

# ----------------------------------------------------------------------------
# 8. Firewall (open backend + frontend ports)
# ----------------------------------------------------------------------------

if command -v ufw >/dev/null 2>&1; then
    log "Opening firewall ports ${BACKEND_PORT} and ${FRONTEND_PORT}"
    ufw allow "${BACKEND_PORT}/tcp" >/dev/null 2>&1 || warn "Could not run 'ufw allow ${BACKEND_PORT}/tcp' (try with sudo)."
    ufw allow "${FRONTEND_PORT}/tcp" >/dev/null 2>&1 || warn "Could not run 'ufw allow ${FRONTEND_PORT}/tcp' (try with sudo)."
else
    warn "ufw not found -- skipping firewall rules. Open ${BACKEND_PORT}/tcp and ${FRONTEND_PORT}/tcp manually if needed."
fi

# ----------------------------------------------------------------------------
# 9. Start backend
# ----------------------------------------------------------------------------

log "Starting backend on port ${BACKEND_PORT}"

if [[ -f "$BACKEND_PID_FILE" ]]; then
    kill "$(cat "$BACKEND_PID_FILE")" >/dev/null 2>&1 || true
    sleep 1
fi

cd "$BACKEND_DIR"
nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" \
    > "$BACKEND_LOG_FILE" 2>&1 &
echo $! > "$BACKEND_PID_FILE"
cd "$SCRIPT_DIR"

sleep 2

curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1 ||
    die "Backend health check failed. Check $BACKEND_LOG_FILE"

# ----------------------------------------------------------------------------
# 10. Start frontend (separate port, proxies /api to the backend)
# ----------------------------------------------------------------------------

log "Starting frontend on port ${FRONTEND_PORT}"

if [[ -f "$FRONTEND_PID_FILE" ]]; then
    kill "$(cat "$FRONTEND_PID_FILE")" >/dev/null 2>&1 || true
    sleep 1
fi

VITE_DEV_PORT="$FRONTEND_PORT" VITE_API_PROXY_TARGET="http://localhost:${BACKEND_PORT}" \
    nohup npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" \
    > "$FRONTEND_LOG_FILE" 2>&1 &
echo $! > "$FRONTEND_PID_FILE"

sleep 3

log "Test instance is running"

cat <<EOF

--------------------------------------------------------------
 ServiceOS test instance
--------------------------------------------------------------
 Frontend: http://localhost:${FRONTEND_PORT}
 Backend:  http://localhost:${BACKEND_PORT}
 Login:    admin / Admin#99

 Database: ${DB_NAME}
 DB user:  ${DB_USER}

 Logs:     $BACKEND_LOG_FILE
           $FRONTEND_LOG_FILE
 Stop:     kill \$(cat $BACKEND_PID_FILE) \$(cat $FRONTEND_PID_FILE)
--------------------------------------------------------------

EOF
