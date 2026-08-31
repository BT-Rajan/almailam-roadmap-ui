#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS Installer -- deploys/updates one of two fixed instances under
# /apps:
#
#   /apps/serviceos     "dev"  -- production build, single pm2 process
#                                 (backend serves the built frontend)
#   /apps/alhadi-test   "test" -- vite dev server, separate pm2 processes
#                                 for backend + frontend
#
# This script does not depend on where it's run from -- it always targets
# /apps/serviceos or /apps/alhadi-test, cloning them from git if they don't
# exist yet. Keep the canonical copy at /apps/install.sh; running the copy
# inside either instance checkout works identically.
#
# Each run:
#   - asks whether to deploy "dev" or "test" (or read --instance=dev|test)
#   - clones the instance dir if missing, otherwise fetches + resets it to
#     the latest origin/main -- code only (backend/.env, venv/, node_modules,
#     dist/ and the pm2 ecosystem file are all gitignored and untouched)
#   - never creates a database, never writes backend/.env -- both instances
#     already have their DB and .env configured; this script assumes that
#     and fails loudly if backend/.env is missing rather than guessing
#   - applies any backend/migrations/*.sql files not yet recorded in
#     schema_migrations -- additive only, never drops/recreates the
#     database or touches existing rows
#   - reinstalls dependencies and (re)starts the instance under pm2
#
# Usage:
#   ./install.sh                   interactive: asks "dev" or "test"
#   ./install.sh --instance=dev
#   ./install.sh --instance=test
#   ./install.sh --instance=dev --yes
# ============================================================================

APPS_DIR="/apps"
REPO_URL="https://github.com/BT-Rajan/almailam-roadmap-ui.git"
BRANCH="main"

DEFAULT_DB_HOST="localhost"
DEFAULT_DB_PORT="3306"
DEFAULT_DB_USER="app_user"
DEFAULT_DB_PASSWORD="Chennai#44"

INSTANCE=""
ASSUME_YES=false

# ----------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------

for arg in "$@"; do
    case "$arg" in
        --instance=dev)
            INSTANCE="dev"
            ;;

        --instance=test)
            INSTANCE="test"
            ;;

        --yes|-y)
            ASSUME_YES=true
            ;;

        -h|--help)
            cat <<EOF

ServiceOS installer

Usage:
  ./install.sh
  ./install.sh --instance=dev
  ./install.sh --instance=test
  ./install.sh --instance=dev --yes

Options:
  --instance=dev|test   Select the instance without prompting
  --yes                 Non-interactive mode (requires --instance)
  -y                    Same as --yes
  -h, --help            Show this help

Instances:
  dev   -> /apps/serviceos    production build, single pm2 process
  test  -> /apps/alhadi-test  vite dev server, backend+frontend pm2 processes

This script never creates a database and never writes backend/.env -- both
instances must already have those configured. Database changes go through
backend/migrations/*.sql, applied additively on every run.

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

# ----------------------------------------------------------------------------
# 1. Which instance?
# ----------------------------------------------------------------------------

if [[ -z "$INSTANCE" ]]; then
    if [[ "$ASSUME_YES" == true ]]; then
        die "Non-interactive mode requires --instance=dev or --instance=test"
    fi

    echo
    echo "Which instance do you want to install/update?"
    echo "  dev   -> /apps/serviceos    (production build)"
    echo "  test  -> /apps/alhadi-test  (vite dev server)"
    answer="$(ask "Select [dev/test]: " "")"

    case "$answer" in
        dev|Dev|DEV)   INSTANCE="dev" ;;
        test|Test|TEST) INSTANCE="test" ;;
        *) die "Invalid selection: '$answer' (expected 'dev' or 'test')" ;;
    esac
fi

case "$INSTANCE" in
    dev)
        INSTANCE_NAME="serviceos"
        PM2_MODE="single"
        DEFAULT_BACKEND_PORT="8000"
        ;;
    test)
        INSTANCE_NAME="alhadi-test"
        PM2_MODE="split"
        DEFAULT_BACKEND_PORT="8888"
        FRONTEND_PORT="9007"
        ;;
    *)
        die "Invalid instance: $INSTANCE (expected 'dev' or 'test')"
        ;;
esac

INSTANCE_DIR="$APPS_DIR/$INSTANCE_NAME"
BACKEND_DIR="$INSTANCE_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"

log "Instance: $INSTANCE -> $INSTANCE_DIR"

# ----------------------------------------------------------------------------
# 2. Basic packages
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

NODE_VERSION=20

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

if ! require_cmd pm2; then
    log "Installing PM2"
    npm install -g pm2
else
    log "PM2 already installed: $(pm2 -v)"
fi

# ----------------------------------------------------------------------------
# 3. Pull code (code only -- never touches backend/.env or the database)
# ----------------------------------------------------------------------------

mkdir -p "$APPS_DIR"

if [[ -d "$INSTANCE_DIR" && ! -d "$INSTANCE_DIR/.git" ]]; then
    die "$INSTANCE_DIR exists but is not a git checkout. Investigate/remove it manually, then re-run."
fi

if [[ ! -d "$INSTANCE_DIR/.git" ]]; then
    log "Cloning $REPO_URL ($BRANCH) into $INSTANCE_DIR"
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTANCE_DIR"
else
    log "Updating $INSTANCE_DIR to latest $BRANCH"
    git -C "$INSTANCE_DIR" fetch origin "$BRANCH"
    git -C "$INSTANCE_DIR" checkout "$BRANCH"
    git -C "$INSTANCE_DIR" reset --hard "origin/$BRANCH"
    # -fd only, no -x: respects .gitignore, so backend/.env, venv/,
    # node_modules, dist/ and ecosystem*.config.cjs are left alone.
    git -C "$INSTANCE_DIR" clean -fd
fi

# ----------------------------------------------------------------------------
# 4. Database configuration -- read only, never written by this script
# ----------------------------------------------------------------------------

log "Reading database configuration"

if [[ ! -f "$ENV_FILE" ]]; then
    die "$ENV_FILE not found. This installer does not create it -- set up backend/.env for this instance first (DB credentials, JWT secret, PORT), then re-run."
fi

DB_HOST="$(get_env DB_HOST "$DEFAULT_DB_HOST")"
DB_PORT="$(get_env DB_PORT "$DEFAULT_DB_PORT")"
DB_NAME="$(get_env DB_NAME "")"
DB_USER="$(get_env DB_USER "$DEFAULT_DB_USER")"
DB_PASSWORD="$(get_env DB_PASSWORD "$DEFAULT_DB_PASSWORD")"
BACKEND_PORT="$(get_env PORT "$DEFAULT_BACKEND_PORT")"

if [[ -z "$DB_NAME" ]]; then
    die "DB_NAME is not set in $ENV_FILE."
fi

log "Backend port: $BACKEND_PORT (from $ENV_FILE)"

# ----------------------------------------------------------------------------
# 5. MariaDB / MySQL
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

log "Testing database connection"

# MYSQL_PWD avoids exposing the password in the command line.
export MYSQL_PWD="$DB_PASSWORD"

if ! "$DB_CLIENT" \
        --protocol=tcp \
        -h "$DB_HOST" \
        -P "$DB_PORT" \
        -u "$DB_USER" \
        "$DB_NAME" \
        -e "SELECT 1;" >/dev/null 2>&1; then

    unset MYSQL_PWD
    die "Cannot connect to database '$DB_NAME' as ${DB_USER}@${DB_HOST}:${DB_PORT}. This installer does not create databases or users -- confirm $ENV_FILE and the database itself are already set up correctly."
fi

log "Database connection successful"

# ----------------------------------------------------------------------------
# 6. Apply pending migrations (additive only -- never drops/recreates the
#    database, never touches existing rows)
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

        log "Applying database migrations"

        # Tracks which migration files have already been run against this
        # database, so re-running install.sh skips them instead of
        # replaying every .sql file from scratch every time. Each
        # migration is still written to be idempotent on its own
        # (information_schema-guarded ADD COLUMN, etc.) -- this table is a
        # second, cheaper line of defense: skip the whole file rather than
        # rely on every statement inside it tolerating a second run.
        "$DB_CLIENT" \
            --protocol=tcp \
            -h "$DB_HOST" \
            -P "$DB_PORT" \
            -u "$DB_USER" \
            "$DB_NAME" <<< "
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename VARCHAR(255) NOT NULL PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            "

        for migration in "${MIGRATIONS[@]}"; do

            migration_name="$(basename "$migration")"

            already_applied="$(
                "$DB_CLIENT" \
                    --protocol=tcp \
                    -h "$DB_HOST" \
                    -P "$DB_PORT" \
                    -u "$DB_USER" \
                    -N -s \
                    "$DB_NAME" <<< "
                        SELECT COUNT(*) FROM schema_migrations WHERE filename = '$migration_name';
                    "
            )"

            if [[ "$already_applied" != "0" ]]; then
                log "Migration: $migration_name (already applied, skipping)"
                continue
            fi

            log "Migration: $migration_name"

            "$DB_CLIENT" \
                --protocol=tcp \
                -h "$DB_HOST" \
                -P "$DB_PORT" \
                -u "$DB_USER" \
                "$DB_NAME" < "$migration"

            "$DB_CLIENT" \
                --protocol=tcp \
                -h "$DB_HOST" \
                -P "$DB_PORT" \
                -u "$DB_USER" \
                "$DB_NAME" <<< "
                    INSERT INTO schema_migrations (filename) VALUES ('$migration_name');
                "
        done

        log "All migrations completed"

    else
        log "No migrations found"
    fi

else
    log "No backend/migrations directory"
fi

unset MYSQL_PWD

# ----------------------------------------------------------------------------
# 7. Python backend
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
# 8. Admin user (idempotent -- skips if it already exists)
# ----------------------------------------------------------------------------

if [[ -f "$BACKEND_DIR/scripts/create_admin.py" ]]; then

    log "Checking admin user"

    python -m scripts.create_admin --quick-start ||
        warn "Admin creation skipped/failed. Check the output above."

fi

deactivate || true

cd "$INSTANCE_DIR"

# ----------------------------------------------------------------------------
# 9. Frontend
# ----------------------------------------------------------------------------

log "Installing frontend dependencies"

npm install

if [[ "$PM2_MODE" == "single" ]]; then
    log "Building frontend"
    npm run build
fi

# ----------------------------------------------------------------------------
# 10. Firewall (test instance only -- opens backend + frontend ports)
# ----------------------------------------------------------------------------

if [[ "$PM2_MODE" == "split" ]]; then
    if require_cmd ufw; then
        log "Opening firewall ports ${BACKEND_PORT} and ${FRONTEND_PORT}"
        ufw allow "${BACKEND_PORT}/tcp" >/dev/null 2>&1 || warn "Could not run 'ufw allow ${BACKEND_PORT}/tcp' (try with sudo)."
        ufw allow "${FRONTEND_PORT}/tcp" >/dev/null 2>&1 || warn "Could not run 'ufw allow ${FRONTEND_PORT}/tcp' (try with sudo)."
    else
        warn "ufw not found -- skipping firewall rules. Open ${BACKEND_PORT}/tcp and ${FRONTEND_PORT}/tcp manually if needed."
    fi
fi

# ----------------------------------------------------------------------------
# 11. PM2
# ----------------------------------------------------------------------------

log "Configuring PM2"

if [[ "$PM2_MODE" == "single" ]]; then

    PM2_APP_NAME="serviceos"
    ECOSYSTEM_FILE="$INSTANCE_DIR/ecosystem.config.cjs"

    cat > "$ECOSYSTEM_FILE" <<EOF
module.exports = {
    apps: [
        {
            name: "serviceos",
            cwd: "${BACKEND_DIR}",
            script: "${BACKEND_DIR}/venv/bin/uvicorn",
            args: "app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}",
            interpreter: "none",

            env: {
                PORT: "${BACKEND_PORT}"
            },

            autorestart: true,
            max_restarts: 10,
            restart_delay: 3000
        }
    ]
};
EOF

    if pm2 describe "$PM2_APP_NAME" >/dev/null 2>&1; then
        log "Restarting existing ServiceOS process"
        pm2 restart "$ECOSYSTEM_FILE" --update-env
    else
        log "Starting ServiceOS"
        pm2 start "$ECOSYSTEM_FILE"
    fi

else

    PM2_BACKEND_NAME="alhadi-test-backend"
    PM2_FRONTEND_NAME="alhadi-test-frontend"
    ECOSYSTEM_FILE="$INSTANCE_DIR/ecosystem.config.cjs"

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
            cwd: "${INSTANCE_DIR}",
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

    for name in "$PM2_BACKEND_NAME" "$PM2_FRONTEND_NAME"; do
        if pm2 describe "$name" >/dev/null 2>&1; then
            pm2 delete "$name" >/dev/null 2>&1 || true
        fi
    done

    log "Starting alhadi-test under PM2"
    pm2 start "$ECOSYSTEM_FILE"

fi

pm2 save

# ----------------------------------------------------------------------------
# 12. Health check(s)
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

if [[ "$BACKEND_UP" == true ]]; then
    log "Backend health check passed"
else
    warn "Backend health endpoint did not respond after 20s."
    echo
    echo "Check:"
    echo "  pm2 status"
    if [[ "$PM2_MODE" == "single" ]]; then
        echo "  pm2 logs serviceos"
    else
        echo "  pm2 logs alhadi-test-backend"
    fi
fi

if [[ "$PM2_MODE" == "split" ]]; then

    log "Checking frontend"

    FRONTEND_UP=false
    for _ in $(seq 1 20); do
        if curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null 2>&1; then
            FRONTEND_UP=true
            break
        fi
        sleep 1
    done

    if [[ "$FRONTEND_UP" == true ]]; then
        log "Frontend health check passed"
    else
        warn "Frontend not responding yet after 20s. Check: pm2 logs alhadi-test-frontend"
    fi

fi

# ----------------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------------

log "$INSTANCE_NAME setup complete"

if [[ "$PM2_MODE" == "single" ]]; then

    cat <<EOF

ServiceOS (dev)
---------------

Directory:
  ${INSTANCE_DIR}

URL:
  http://localhost:${BACKEND_PORT}

Health:
  http://localhost:${BACKEND_PORT}/api/health

Database:
  Host:     ${DB_HOST}
  Port:     ${DB_PORT}
  Database: ${DB_NAME}
  User:     ${DB_USER}

PM2:
  pm2 status
  pm2 logs serviceos
  pm2 restart serviceos

Re-run any time to pull the latest main + apply new migrations:
  ./install.sh --instance=dev

EOF

else

    cat <<EOF

ServiceOS (test / alhadi-test)
-------------------------------

Directory:
  ${INSTANCE_DIR}

Frontend: http://localhost:${FRONTEND_PORT}
Backend:  http://localhost:${BACKEND_PORT}

Database:
  Host:     ${DB_HOST}
  Port:     ${DB_PORT}
  Database: ${DB_NAME}
  User:     ${DB_USER}

PM2:
  pm2 status
  pm2 logs alhadi-test-backend
  pm2 logs alhadi-test-frontend
  pm2 restart alhadi-test-backend alhadi-test-frontend

Re-run any time to pull the latest main + apply new migrations:
  ./install.sh --instance=test

EOF

fi
