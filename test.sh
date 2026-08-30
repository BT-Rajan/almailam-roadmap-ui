#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS - Test Instance Setup
#
# Self-running, non-interactive setup for a fresh test instance:
#   - creates database "alhadi-test" + user app_user
#   - loads schema.sql only (no test/demo data)
#   - creates the admin login (admin / Admin#99) and nothing else
#   - builds the frontend and starts the app on one port
#
# Run once on a fresh box:
#   ./test.sh
#
# Re-running is safe: DB/user creation is idempotent, the admin script
# skips if the user already exists, and the server process is restarted.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
PID_FILE="$SCRIPT_DIR/test.pid"
LOG_FILE="$SCRIPT_DIR/test.log"

DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="alhadi-test"
DB_USER="app_user"
DB_PASSWORD="Chennai#44"
PORT="8000"

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }
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

# ----------------------------------------------------------------------------
# 2. Database + user
# ----------------------------------------------------------------------------

log "Creating test database '$DB_NAME'"

ROOT_CLIENT=(--protocol=socket -u root)
if ! "$DB_CLIENT" "${ROOT_CLIENT[@]}" -e "SELECT 1;" >/dev/null 2>&1; then
    ROOT_CLIENT=(--protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u root)
fi

"$DB_CLIENT" "${ROOT_CLIENT[@]}" -e "SELECT 1;" >/dev/null 2>&1 ||
    die "Cannot connect to MariaDB/MySQL as root (socket or tcp). Make sure the DB server is running."

"$DB_CLIENT" "${ROOT_CLIENT[@]}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost'
    IDENTIFIED BY '${DB_PASSWORD}';

ALTER USER '${DB_USER}'@'localhost'
    IDENTIFIED BY '${DB_PASSWORD}';

GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';

FLUSH PRIVILEGES;
SQL

# ----------------------------------------------------------------------------
# 3. Schema (fresh instance -> load schema.sql only, no test data)
# ----------------------------------------------------------------------------

log "Loading schema into '$DB_NAME'"

MYSQL_PWD="$DB_PASSWORD" "$DB_CLIENT" \
    --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" \
    "$DB_NAME" < "$BACKEND_DIR/schema.sql"
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
PORT=${PORT}

DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

CORS_ORIGINS=http://localhost:${PORT}

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
# 7. Frontend build
# ----------------------------------------------------------------------------

log "Building frontend"

npm install
npm run build

# ----------------------------------------------------------------------------
# 8. Start (self running, single process serving API + built frontend)
# ----------------------------------------------------------------------------

log "Starting test server"

if [[ -f "$PID_FILE" ]]; then
    OLD_PID="$(cat "$PID_FILE")"
    kill "$OLD_PID" >/dev/null 2>&1 || true
    sleep 1
fi

cd "$BACKEND_DIR"
nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT" \
    > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
cd "$SCRIPT_DIR"

sleep 2

if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    log "Test instance is running"
else
    die "Health check failed. Check $LOG_FILE"
fi

cat <<EOF

--------------------------------------------------------------
 ServiceOS test instance
--------------------------------------------------------------
 URL:      http://localhost:${PORT}
 Login:    admin / Admin#99

 Database: ${DB_NAME}
 DB user:  ${DB_USER}

 Logs:     $LOG_FILE
 Stop:     kill \$(cat $PID_FILE)
--------------------------------------------------------------

EOF
