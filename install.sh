#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS Installer / Reinstaller
#
# Normal:
#   ./install.sh
#
# Rebuild + apply migrations:
#   ./install.sh --migrate
#
# Non-interactive:
#   ./install.sh --yes
#
# Rebuild + migrations without prompts:
#   ./install.sh --yes --migrate
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"

NODE_VERSION=20
DEFAULT_PORT=8000

# Database defaults
DEFAULT_DB_HOST="localhost"
DEFAULT_DB_PORT="3306"
DEFAULT_DB_NAME="almailan"
DEFAULT_DB_USER="app_user"
DEFAULT_DB_PASSWORD="Chennai#44"

PORT=""
APPLY_MIGRATIONS=false
ASSUME_YES=false

# ----------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------

for arg in "$@"; do
    case "$arg" in
        --port=*)
            PORT="${arg#*=}"
            ;;

        --migrate|--apply-migrations)
            APPLY_MIGRATIONS=true
            ;;

        --yes|-y)
            ASSUME_YES=true
            ;;

        -h|--help)
            cat <<EOF

ServiceOS installer

Usage:
  ./install.sh
  ./install.sh --migrate
  ./install.sh --yes
  ./install.sh --yes --migrate
  ./install.sh --port=8000 --migrate

Options:
  --port=PORT       Set application port
  --migrate         Apply backend/migrations/*.sql
  --yes             Non-interactive mode
  -y                Same as --yes
  -h, --help        Show this help

Database:
  Database settings are read from:
    backend/.env

  If missing, defaults are:

    DB_HOST=localhost
    DB_PORT=3306
    DB_NAME=almailan
    DB_USER=app_user
    DB_PASSWORD=Chennai#44

EOF
            exit 0
            ;;

        *)
            echo "ERROR: Unknown option: $arg" >&2
            exit 1
            ;;
    esac
done

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

log() {
    printf '\n\033[1;32m==> %s\033[0m\n' "$1"
}

warn() {
    printf '\033[1;33m!! %s\033[0m\n' "$1"
}

err() {
    printf '\033[1;31mERROR: %s\033[0m\n' "$1" >&2
}

die() {
    err "$1"
    exit 1
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1
}

ask() {
    local prompt="$1"
    local default="${2:-}"
    local answer

    read -r -p "$prompt" answer || true
    echo "${answer:-$default}"
}

# ----------------------------------------------------------------------------
# .env helpers
# ----------------------------------------------------------------------------

get_env() {
    local key="$1"
    local default="${2:-}"
    local value=""

    if [[ -f "$ENV_FILE" ]]; then
        value="$(
            sed -n \
                -e "s/^${key}=//p" \
                "$ENV_FILE" |
            head -n 1
        )"
    fi

    value="${value%$'\r'}"

    # Remove matching surrounding quotes
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
        value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
        value="${value:1:${#value}-2}"
    fi

    echo "${value:-$default}"
}

set_env() {
    local key="$1"
    local value="$2"

    touch "$ENV_FILE"

    # Escape sed replacement characters
    local escaped
    escaped="$(printf '%s' "$value" | sed 's/[&/\]/\\&/g')"

    if grep -qE "^${key}=" "$ENV_FILE"; then
        sed -i "s|^${key}=.*|${key}=${escaped}|" "$ENV_FILE"
    else
        printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
    fi
}

# ----------------------------------------------------------------------------
# 1. Basic packages
# ----------------------------------------------------------------------------
#
# IMPORTANT:
# This installer does not manage system packages -- no apt-get, no
# package manager calls of any kind, ever. It assumes the target
# machine already has what it needs, the same way the MariaDB/MySQL
# check further down assumes the database is already installed and
# reachable rather than trying to install or configure it. Touching
# apt here (even just "apt-get install" for something missing) risks
# tripping over whatever else is configured on the box -- e.g. a
# third-party repo with a repo-trust/signing issue -- and taking down
# an install that has nothing to do with any of that.
#
# If a required command is missing, install it yourself with your
# system's own package manager, then re-run this installer.
# ----------------------------------------------------------------------------

log "Checking system dependencies"

MISSING_CMDS=()
for cmd in git python3 curl openssl; do
    require_cmd "$cmd" || MISSING_CMDS+=("$cmd")
done

if (( ${#MISSING_CMDS[@]} > 0 )); then
    die "Missing required command(s): ${MISSING_CMDS[*]}. Install them with your system's package manager, then re-run this installer."
fi

log "Found: git, python3, curl, openssl"

# ----------------------------------------------------------------------------
# 2. Node.js
# ----------------------------------------------------------------------------

if ! require_cmd node || \
   [[ "$(node -v | sed 's/^v//' | cut -d. -f1)" -lt "$NODE_VERSION" ]]; then

    log "Installing Node.js ${NODE_VERSION}"

    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

    if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
        curl -fsSL \
            https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh |
            bash
    fi

    # shellcheck disable=SC1090
    source "$NVM_DIR/nvm.sh"

    nvm install "$NODE_VERSION"
    nvm use "$NODE_VERSION"
else
    log "Node.js already installed: $(node -v)"
fi

# Load nvm for subsequent commands
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    source "$NVM_DIR/nvm.sh"
fi

# ----------------------------------------------------------------------------
# 3. PM2
# ----------------------------------------------------------------------------

if ! require_cmd pm2; then
    log "Installing PM2"
    npm install -g pm2
else
    log "PM2 already installed: $(pm2 -v)"
fi

# ----------------------------------------------------------------------------
# 4. Create/read .env
# ----------------------------------------------------------------------------

log "Loading database configuration"

mkdir -p "$BACKEND_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
    log "Creating backend/.env"

    if [[ -f "$BACKEND_DIR/.env.example" ]]; then
        cp "$BACKEND_DIR/.env.example" "$ENV_FILE"
    else
        touch "$ENV_FILE"
    fi

    if ! grep -q '^JWT_SECRET_KEY=' "$ENV_FILE"; then
        set_env JWT_SECRET_KEY "$(openssl rand -hex 32)"
    fi
fi

# Read existing values.
DB_HOST="$(get_env DB_HOST "$DEFAULT_DB_HOST")"
DB_PORT="$(get_env DB_PORT "$DEFAULT_DB_PORT")"
DB_NAME="$(get_env DB_NAME "$DEFAULT_DB_NAME")"
DB_USER="$(get_env DB_USER "$DEFAULT_DB_USER")"
DB_PASSWORD="$(get_env DB_PASSWORD "$DEFAULT_DB_PASSWORD")"

# Preserve/update these values.
set_env DB_HOST "$DB_HOST"
set_env DB_PORT "$DB_PORT"
set_env DB_NAME "$DB_NAME"
set_env DB_USER "$DB_USER"
set_env DB_PASSWORD "$DB_PASSWORD"

# ----------------------------------------------------------------------------
# 5. Port
# ----------------------------------------------------------------------------

CURRENT_PORT="$(get_env PORT "$DEFAULT_PORT")"

if [[ -n "$PORT" ]]; then
    :
elif [[ "$ASSUME_YES" == true ]]; then
    PORT="$CURRENT_PORT"
else
    PORT="$(ask "Application port [${CURRENT_PORT}]: " "$CURRENT_PORT")"
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]] ||
   (( PORT < 1 || PORT > 65535 )); then
    die "Invalid port: $PORT"
fi

set_env PORT "$PORT"

log "Application port: $PORT"

# ----------------------------------------------------------------------------
# 6. MariaDB / MySQL
# ----------------------------------------------------------------------------
#
# IMPORTANT:
# Do NOT require a systemd mysql/mariadb service.
#
# Your server already has:
#
#   /usr/sbin/mariadbd
#
# and it may have been started by another mechanism.
#
# We only need the database to be reachable.
# ----------------------------------------------------------------------------

log "Checking MySQL/MariaDB"

if require_cmd mariadb; then
    DB_CLIENT="mariadb"
elif require_cmd mysql; then
    DB_CLIENT="mysql"
else
    die "Neither mysql nor mariadb client is installed."
fi

log "Database client: $($DB_CLIENT --version)"

# ----------------------------------------------------------------------------
# 7. Database connection
# ----------------------------------------------------------------------------

log "Testing database connection"

# MYSQL_PWD avoids exposing the password in the command line.
export MYSQL_PWD="$DB_PASSWORD"

if "$DB_CLIENT" \
        --protocol=tcp \
        -h "$DB_HOST" \
        -P "$DB_PORT" \
        -u "$DB_USER" \
        -e "SELECT 1;" >/dev/null 2>&1; then

    log "Database connection successful"

else

    warn "Application database credentials could not connect."

    echo
    echo "Database:"
    echo "  Host:     $DB_HOST"
    echo "  Port:     $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User:     $DB_USER"
    echo

    # Try root/admin connection only to create the application database/user.
    ROOT_CLIENT=()

    if [[ -n "${MYSQL_ROOT_PASSWORD:-}" ]]; then
        export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
        ROOT_CLIENT=(
            --protocol=tcp
            -h "$DB_HOST"
            -P "$DB_PORT"
            -u root
        )
    else
        unset MYSQL_PWD
        ROOT_CLIENT=(
            --protocol=socket
            -u root
        )
    fi

    if "$DB_CLIENT" "${ROOT_CLIENT[@]}" -e "SELECT 1;" >/dev/null 2>&1; then

        log "Administrative database access available"

        # Escape values for SQL.
        SQL_DB="$(printf '%s' "$DB_NAME" | sed "s/'/''/g")"
        SQL_USER="$(printf '%s' "$DB_USER" | sed "s/'/''/g")"
        SQL_PASS="$(printf '%s' "$DB_PASSWORD" | sed "s/'/''/g")"

        "$DB_CLIENT" "${ROOT_CLIENT[@]}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${SQL_USER}'@'localhost'
    IDENTIFIED BY '${SQL_PASS}';

ALTER USER '${SQL_USER}'@'localhost'
    IDENTIFIED BY '${SQL_PASS}';

GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${SQL_USER}'@'localhost';

FLUSH PRIVILEGES;
SQL

        log "Database and application user verified"

    else

        unset MYSQL_PWD

        die "Cannot connect to MariaDB/MySQL as ${DB_USER}, and root administrative access is unavailable."
    fi
fi

unset MYSQL_PWD

# ----------------------------------------------------------------------------
# 8. Apply migrations
# ----------------------------------------------------------------------------

if [[ -d "$BACKEND_DIR/migrations" ]]; then

    mapfile -t MIGRATIONS < <(
        find "$BACKEND_DIR/migrations" \
            -maxdepth 1 \
            -type f \
            -name '*.sql' \
            -print |
        sort
    )

    if (( ${#MIGRATIONS[@]} > 0 )); then

        RUN_MIGRATIONS="$APPLY_MIGRATIONS"

        if [[ "$RUN_MIGRATIONS" == false && "$ASSUME_YES" == false ]]; then

            echo
            echo "Found ${#MIGRATIONS[@]} database migration(s)."

            if [[ "$(ask "Apply migrations now? [y/N]: " "n")" =~ ^[Yy]$ ]]; then
                RUN_MIGRATIONS=true
            fi
        fi

        if [[ "$RUN_MIGRATIONS" == true ]]; then

            log "Applying database migrations"

            export MYSQL_PWD="$DB_PASSWORD"

            for migration in "${MIGRATIONS[@]}"; do

                log "Migration: $(basename "$migration")"

                "$DB_CLIENT" \
                    --protocol=tcp \
                    -h "$DB_HOST" \
                    -P "$DB_PORT" \
                    -u "$DB_USER" \
                    "$DB_NAME" < "$migration"
            done

            unset MYSQL_PWD

            log "All migrations completed"

        else
            log "Migrations skipped"
        fi
    else
        log "No migrations found"
    fi

else
    log "No backend/migrations directory"
fi

# ----------------------------------------------------------------------------
# 9. Python backend
# ----------------------------------------------------------------------------

log "Setting up Python backend"

cd "$BACKEND_DIR"

if [[ ! -d venv ]]; then
    python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# ----------------------------------------------------------------------------
# 10. Admin user
# ----------------------------------------------------------------------------

if [[ -f "$BACKEND_DIR/scripts/create_admin.py" ]]; then

    log "Checking admin user"

    python -m scripts.create_admin --quick-start ||
        warn "Admin creation skipped/failed. Check the output above."

fi

deactivate || true

cd "$SCRIPT_DIR"

# ----------------------------------------------------------------------------
# 11. Frontend
# ----------------------------------------------------------------------------

log "Installing frontend dependencies"

npm install

log "Building frontend"

npm run build

# ----------------------------------------------------------------------------
# 12. PM2
# ----------------------------------------------------------------------------

log "Configuring PM2"

cat > "$SCRIPT_DIR/ecosystem.config.cjs" <<EOF
module.exports = {
    apps: [
        {
            name: "serviceos",
            cwd: "${BACKEND_DIR}",
            script: "${BACKEND_DIR}/venv/bin/uvicorn",
            args: "app.main:app --host 0.0.0.0 --port ${PORT}",
            interpreter: "none",

            env: {
                PORT: "${PORT}"
            },

            autorestart: true,
            max_restarts: 10,
            restart_delay: 3000
        }
    ]
};
EOF

if pm2 describe serviceos >/dev/null 2>&1; then

    log "Restarting existing ServiceOS process"

    pm2 restart ecosystem.config.cjs --update-env

else

    log "Starting ServiceOS"

    pm2 start ecosystem.config.cjs

fi

pm2 save

# ----------------------------------------------------------------------------
# 13. Final health check
# ----------------------------------------------------------------------------

log "Checking ServiceOS"

sleep 2

if curl -fsS \
    "http://127.0.0.1:${PORT}/api/health" \
    >/dev/null 2>&1; then

    log "ServiceOS health check passed"

else

    warn "Health endpoint did not respond yet."

    echo
    echo "Check:"
    echo "  pm2 status"
    echo "  pm2 logs serviceos"
fi

# ----------------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------------

log "ServiceOS setup complete"

cat <<EOF

ServiceOS
---------

URL:
  http://localhost:${PORT}

Health:
  http://localhost:${PORT}/api/health

Database:
  Host:     ${DB_HOST}
  Port:     ${DB_PORT}
  Database: ${DB_NAME}
  User:     ${DB_USER}

PM2:
  pm2 status
  pm2 logs serviceos
  pm2 restart serviceos

After pulling code:
  ./install.sh

Pull + rebuild + migrations:
  ./install.sh --migrate

Non-interactive:
  ./install.sh --yes

Non-interactive + migrations:
  ./install.sh --yes --migrate

EOF
