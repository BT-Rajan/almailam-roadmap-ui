#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS - Test Instance Setup
#
# Self-running, non-interactive setup for a fresh test instance:
#   - connects only as app_user (no root DB access on this server)
#   - drops + recreates database "alhadi-test" on every run (disposable
#     test DB -- schema.sql's seed inserts aren't idempotent, so this is
#     simpler and more reliable than trying to reuse an existing one)
#   - loads schema.sql only (no test/demo data)
#   - creates the admin login (admin / Admin#99) and nothing else
#   - opens firewall ports 8888 (backend) and 9007 (frontend) via ufw
#   - runs backend (8888) and frontend dev server (9007) under PM2 as
#     "alhadi-test-backend" / "alhadi-test-frontend"
#
# Run any time you want a clean slate:
#   ./test.sh
#
# Every run wipes and rebuilds the database from schema.sql -- don't run
# this against anything you want to keep.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
ECOSYSTEM_FILE="$SCRIPT_DIR/ecosystem.alhadi-test.config.cjs"

PM2_BACKEND_NAME="alhadi-test-backend"
PM2_FRONTEND_NAME="alhadi-test-frontend"

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

if ! command -v pm2 >/dev/null 2>&1; then
    log "Installing PM2"
    npm install -g pm2
fi

APP_CLIENT=(--protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER")

# ----------------------------------------------------------------------------
# 2. Database (connect as app_user only -- no root access on this server)
# ----------------------------------------------------------------------------

log "Connecting as ${DB_USER}"

MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" "${APP_CLIENT[@]}" -e "SELECT 1;" >/dev/null 2>&1 ||
    die "Cannot connect as ${DB_USER}/${DB_PASSWORD}. Confirm this user exists and can log in from localhost."

# This is a disposable test instance -- schema.sql has a handful of
# non-idempotent seed INSERTs (permit catalog, activity categories), so
# re-running against a database that already has data in it fails with
# duplicate-key errors. Drop and recreate on every run instead of trying
# to reuse whatever's there.
log "Resetting database '$DB_NAME'"

MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" "${APP_CLIENT[@]}" -e "
    DROP DATABASE IF EXISTS \`${DB_NAME}\`;
    CREATE DATABASE \`${DB_NAME}\`
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;
" || die "Could not reset database '${DB_NAME}' as ${DB_USER} -- confirm this user has DROP/CREATE privileges on it."

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
# 9. PM2 ecosystem (backend + frontend as separate, named apps)
# ----------------------------------------------------------------------------

log "Writing PM2 ecosystem file"

cat > "$ECOSYSTEM_FILE" <<EOF
module.exports = {
    apps: [
        {
            name: "${PM2_BACKEND_NAME}",
            cwd: "${BACKEND_DIR}",
            script: "${BACKEND_DIR}/venv/bin/uvicorn",
            args: "app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}",
            interpreter: "none",
            autorestart: true,
            max_restarts: 10,
            restart_delay: 3000
        },
        {
            name: "${PM2_FRONTEND_NAME}",
            cwd: "${SCRIPT_DIR}",
            script: "npm",
            args: "run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT}",
            interpreter: "none",
            env: {
                VITE_DEV_PORT: "${FRONTEND_PORT}",
                VITE_API_PROXY_TARGET: "http://localhost:${BACKEND_PORT}"
            },
            autorestart: true,
            max_restarts: 10,
            restart_delay: 3000
        }
    ]
};
EOF

# ----------------------------------------------------------------------------
# 10. Start under PM2
# ----------------------------------------------------------------------------

log "Starting under PM2"

for name in "$PM2_BACKEND_NAME" "$PM2_FRONTEND_NAME"; do
    if pm2 describe "$name" >/dev/null 2>&1; then
        pm2 delete "$name" >/dev/null 2>&1 || true
    fi
done

pm2 start "$ECOSYSTEM_FILE"
pm2 save

# ----------------------------------------------------------------------------
# 11. Health checks (retry -- first boot can be slower than a fixed sleep)
# ----------------------------------------------------------------------------

log "Checking backend"

BACKEND_UP=false
for _ in $(seq 1 20); do
    if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
        BACKEND_UP=true
        break
    fi
    sleep 1
done

[[ "$BACKEND_UP" == true ]] ||
    die "Backend health check failed after 20s. Check: pm2 logs ${PM2_BACKEND_NAME}"

log "Checking frontend"

FRONTEND_UP=false
for _ in $(seq 1 20); do
    if curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null 2>&1; then
        FRONTEND_UP=true
        break
    fi
    sleep 1
done

[[ "$FRONTEND_UP" == true ]] ||
    warn "Frontend not responding yet after 20s. Check: pm2 logs ${PM2_FRONTEND_NAME}"

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

 PM2:
   pm2 status
   pm2 logs ${PM2_BACKEND_NAME}
   pm2 logs ${PM2_FRONTEND_NAME}
   pm2 restart ${PM2_BACKEND_NAME} ${PM2_FRONTEND_NAME}
   pm2 delete ${PM2_BACKEND_NAME} ${PM2_FRONTEND_NAME}
--------------------------------------------------------------

EOF
