#!/usr/bin/env bash
#
# install.sh — Interactive installer for ServiceOS (almailam-roadmap-ui) on Ubuntu.
#
# Walks you through:
#   - System packages (Python, MySQL, Node via nvm, build tools, pm2)
#   - The port the whole app runs on (asked once, applied everywhere)
#   - Database setup: fresh install / reuse an existing DB / restore a .sql
#     dump you provide -- safe to re-run any time
#   - Backend virtualenv + dependencies + backend/.env
#   - Frontend build (single production bundle, no separate dev server)
#   - Registering a single pm2 process that serves the API and the built
#     frontend together on the one port you chose
#
# Re-running this script is safe: it will offer to keep or change your port,
# and will not overwrite an existing DB or .env unless you ask it to.
#
# Non-interactive flags (optional, for scripted use -- omit them for the
# normal interactive prompts):
#   --port=NNNN                  Use this port without prompting
#   --db-mode=fresh|reuse|dump   Skip the DB menu
#   --dump-file=PATH             .sql file to restore (with --db-mode=dump)
#   --with-testdata              Load backend/testdata.sql (fresh mode only)
#   --yes                        Accept defaults for any remaining prompt
#   -h, --help
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_DIR="$SCRIPT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"
DB_NAME_DEFAULT="almailam"
NODE_VERSION="20"

# ---------------------------------------------------------------------------
# Flags (all optional -- interactive prompts fill in anything not passed)
# ---------------------------------------------------------------------------
PORT_ARG=""
DB_MODE_ARG=""
DUMP_FILE_ARG=""
WITH_TESTDATA=false
ASSUME_YES=false

for arg in "$@"; do
  case "$arg" in
    --port=*) PORT_ARG="${arg#*=}" ;;
    --db-mode=*) DB_MODE_ARG="${arg#*=}" ;;
    --dump-file=*) DUMP_FILE_ARG="${arg#*=}" ;;
    --with-testdata) WITH_TESTDATA=true ;;
    --yes) ASSUME_YES=true ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^#//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

log()   { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }
warn()  { printf '\033[1;33m!! %s\033[0m\n' "$1"; }
err()   { printf '\033[1;31mERROR: %s\033[0m\n' "$1" >&2; }
ask()   { local prompt="$1" def="${2:-}" reply; read -rp "$prompt" reply || true; echo "${reply:-$def}"; }
require_cmd() { command -v "$1" >/dev/null 2>&1; }

# Add or update KEY=VALUE in an env file, preserving everything else already
# in it. Creates the key if it isn't there yet. This is what lets the
# installer be re-run without clobbering values (like AI API keys) you
# already set by hand.
set_env_var() {
  local file="$1" key="$2" value="$3"
  local escaped
  escaped="$(printf '%s' "$value" | sed -e 's/[\/&]/\\&/g')"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    sed -i "s/^${key}=.*/${key}=${escaped}/" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

# ===========================================================================
# 1. System packages
# ===========================================================================
log "Installing base system packages (git, python3, build tools)"
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip build-essential curl

# ---------------------------------------------------------------------------
# MySQL-compatible database server
# ---------------------------------------------------------------------------
# Some hosts (and most cloud images) ship MariaDB, which is a drop-in
# replacement and already provides the `mysql` client + a MySQL-protocol
# server -- installing mysql-server on top of it is unnecessary and some
# providers actively block it. Only install mysql-server if neither MySQL
# nor MariaDB is already present; otherwise use whatever's already there.
DB_SERVICE=""
if require_cmd mysql || require_cmd mariadb; then
  log "MySQL-compatible server already present ($(mysql --version 2>/dev/null || mariadb --version)) — skipping mysql-server install"
elif dpkg -l 2>/dev/null | grep -qE '^ii\s+(mariadb-server|mysql-server)'; then
  log "Database server package already installed — skipping mysql-server install"
else
  log "Installing mysql-server"
  sudo apt install -y mysql-server
fi

for candidate in mysql mariadb; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${candidate}.service"; then
    DB_SERVICE="$candidate"
    break
  fi
done
if [ -z "$DB_SERVICE" ]; then
  err "Could not find a mysql.service or mariadb.service to manage. Make sure a MySQL-compatible server is installed and try again."
  exit 1
fi
log "Using ${DB_SERVICE} as the database service"

if require_cmd mysql; then
  DB_CLIENT="mysql"
elif require_cmd mariadb; then
  DB_CLIENT="mariadb"
else
  err "No mysql or mariadb client binary found after install. Install one (e.g. mariadb-client) and re-run."
  exit 1
fi

# ---------------------------------------------------------------------------
# Node.js via nvm
# ---------------------------------------------------------------------------
if ! require_cmd node || [ "$(node -v | sed 's/v//;s/\..*//')" -lt "$NODE_VERSION" ] 2>/dev/null; then
  log "Installing Node.js ${NODE_VERSION} via nvm"
  if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  fi
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1091
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm install "$NODE_VERSION"
  nvm use "$NODE_VERSION"
else
  log "Node.js already installed: $(node -v)"
fi

export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && nvm use "$NODE_VERSION" >/dev/null 2>&1 || true

if ! require_cmd pm2; then
  log "Installing pm2 globally"
  npm install -g pm2
else
  log "pm2 already installed: $(pm2 -v)"
fi

# ===========================================================================
# 2. Port -- asked once, applied everywhere (backend/.env, CORS, pm2)
# ===========================================================================
log "Port configuration"
CURRENT_PORT=""
[ -f "$ENV_FILE" ] && CURRENT_PORT="$(grep -E '^PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || true)"
PORT_DEFAULT="${CURRENT_PORT:-8000}"

if [ -n "$PORT_ARG" ]; then
  PORT="$PORT_ARG"
elif [ "$ASSUME_YES" = true ]; then
  PORT="$PORT_DEFAULT"
else
  echo "ServiceOS runs as a single process on a single port (API + frontend together)."
  while true; do
    PORT="$(ask "Port to run on [${PORT_DEFAULT}]: " "$PORT_DEFAULT")"
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
      err "Enter a number between 1 and 65535."
      continue
    fi
    if require_cmd ss && ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":${PORT}\$"; then
      warn "Something is already listening on port ${PORT}."
      [ "$(ask "Use it anyway? [y/N]: " "n")" =~ ^[Yy] ] && break || continue
    fi
    break
  done
fi
log "Using port ${PORT}"

# ===========================================================================
# 3. Database -- fresh install / reuse an existing DB / restore a dump
# ===========================================================================
log "Database setup"
DB_NAME="$DB_NAME_DEFAULT"
[ -f "$ENV_FILE" ] && DB_NAME="$(grep -E '^DB_NAME=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "$DB_NAME_DEFAULT")"
[ -z "$DB_NAME" ] && DB_NAME="$DB_NAME_DEFAULT"

DB_MODE="$DB_MODE_ARG"
if [ -z "$DB_MODE" ]; then
  if [ "$ASSUME_YES" = true ]; then
    DB_MODE="reuse"
  else
    echo "How do you want to set up the database this time?"
    echo "  1) Fresh install  -- create '${DB_NAME}' and load backend/schema.sql"
    echo "  2) Reuse existing -- database is already set up, just connect to it"
    echo "  3) Restore a dump -- I have a .sql file to import (e.g. from another environment)"
    while true; do
      choice="$(ask "Choice [1/2/3]: " "2")"
      case "$choice" in
        1) DB_MODE="fresh"; break ;;
        2) DB_MODE="reuse"; break ;;
        3) DB_MODE="dump"; break ;;
        *) err "Enter 1, 2, or 3." ;;
      esac
    done
  fi
fi

MYSQL_PWD_INPUT=""
if [ "$DB_MODE" != "reuse" ]; then
  sudo systemctl enable --now "$DB_SERVICE"
  read -rsp "MySQL root password (blank if none set yet): " MYSQL_PWD_INPUT
  echo
  if [ -n "$MYSQL_PWD_INPUT" ]; then
    MYSQL_AUTH=(-u root -p"$MYSQL_PWD_INPUT")
  else
    MYSQL_AUTH=(-u root)
  fi

  sudo "$DB_CLIENT" "${MYSQL_AUTH[@]}" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARSET=utf8mb4;"

  case "$DB_MODE" in
    fresh)
      log "Loading schema into '${DB_NAME}'"
      sudo "$DB_CLIENT" "${MYSQL_AUTH[@]}" "${DB_NAME}" < backend/schema.sql
      if [ "$WITH_TESTDATA" = false ] && [ "$ASSUME_YES" = false ]; then
        [ "$(ask "Load sample test data too? [y/N]: " "n")" =~ ^[Yy] ] && WITH_TESTDATA=true
      fi
      if [ "$WITH_TESTDATA" = true ]; then
        log "Loading test data"
        sudo "$DB_CLIENT" "${MYSQL_AUTH[@]}" "${DB_NAME}" < backend/testdata.sql
      fi
      ;;
    dump)
      DUMP_FILE="$DUMP_FILE_ARG"
      if [ -z "$DUMP_FILE" ]; then
        while true; do
          DUMP_FILE="$(ask "Path to the .sql dump file to restore: " "")"
          [ -f "$DUMP_FILE" ] && break
          err "File not found: ${DUMP_FILE}"
        done
      elif [ ! -f "$DUMP_FILE" ]; then
        err "Dump file not found: ${DUMP_FILE}"
        exit 1
      fi
      log "Restoring dump into '${DB_NAME}' (this replaces existing data in that database)"
      sudo "$DB_CLIENT" "${MYSQL_AUTH[@]}" "${DB_NAME}" < "$DUMP_FILE"
      ;;
  esac
else
  warn "Reusing existing database '${DB_NAME}' -- skipping create/schema/dump."
fi

# ===========================================================================
# 3b. Apply any pending migrations (backend/migrations/*.sql)
# ===========================================================================
# schema.sql only reflects a fresh install; existing databases (reuse mode,
# or a fresh/dump install from before a schema change landed) need these
# applied too. Each migration is written to be idempotent, so it's safe to
# always run this rather than trying to track what's already applied.
if [ -d "$SCRIPT_DIR/backend/migrations" ] && [ -n "$(ls -A "$SCRIPT_DIR/backend/migrations"/*.sql 2>/dev/null)" ]; then
  log "Applying database migrations"
  if [ "$DB_MODE" = "reuse" ] && [ -z "$MYSQL_PWD_INPUT" ]; then
    read -rsp "MySQL root password (blank if none set yet): " MYSQL_PWD_INPUT
    echo
    if [ -n "$MYSQL_PWD_INPUT" ]; then
      MYSQL_AUTH=(-u root -p"$MYSQL_PWD_INPUT")
    else
      MYSQL_AUTH=(-u root)
    fi
  fi
  for migration in "$SCRIPT_DIR"/backend/migrations/*.sql; do
    log "  -> $(basename "$migration")"
    sudo "$DB_CLIENT" "${MYSQL_AUTH[@]}" "${DB_NAME}" < "$migration"
  done
fi

# ===========================================================================
# 4. Backend: venv + deps + .env
# ===========================================================================
log "Setting up backend virtualenv"
cd "$BACKEND_DIR"
[ -d venv ] || python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  log "Creating backend/.env from .env.example"
  cp .env.example .env
  JWT_SECRET="$(openssl rand -hex 32)"
  set_env_var .env JWT_SECRET_KEY "$JWT_SECRET"
  warn "backend/.env created with a generated JWT secret. Add ANTHROPIC_API_KEY / DEEPSEEK_API_KEY yourself to enable AI features."
else
  log "Updating existing backend/.env (port + DB name only -- everything else, including any AI keys, is left as-is)"
fi

set_env_var .env PORT "$PORT"
set_env_var .env DB_NAME "$DB_NAME"
[ -n "$MYSQL_PWD_INPUT" ] && set_env_var .env DB_PASSWORD "$MYSQL_PWD_INPUT"

log "Creating admin user (admin / Admin#99) if not already present"
python -m scripts.create_admin --quick-start || warn "Admin user step failed or already exists — check output above."

deactivate
cd "$SCRIPT_DIR"

# ===========================================================================
# 5. Frontend: build a single production bundle (no separate dev server)
# ===========================================================================
log "Installing frontend dependencies"
npm install

log "Building frontend (dist/) -- this is what the backend will serve"
npm run build

# ===========================================================================
# 6. pm2 -- one process, one port
# ===========================================================================
log "Writing pm2 ecosystem file"
cat > "$SCRIPT_DIR/ecosystem.config.cjs" <<EOF
module.exports = {
  apps: [
    {
      name: 'serviceos',
      cwd: '${BACKEND_DIR}',
      script: '${BACKEND_DIR}/venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port ${PORT}',
      interpreter: 'none',
      env: {
        PORT: '${PORT}',
      },
      autorestart: true,
      max_restarts: 10,
    },
  ],
};
EOF

if pm2 describe serviceos >/dev/null 2>&1; then
  log "Restarting existing pm2 process 'serviceos'"
  pm2 restart ecosystem.config.cjs --update-env
else
  log "Starting pm2 process 'serviceos'"
  pm2 start ecosystem.config.cjs
fi
pm2 save

# ===========================================================================
# Done
# ===========================================================================
log "Setup complete!"
cat <<EOF

ServiceOS is running as a single process on a single port under pm2.

  URL:                http://localhost:${PORT}
  Health check:        curl http://localhost:${PORT}/api/health
  Login:               admin / Admin#99 (change this after first login)

  pm2 status:          pm2 status
  pm2 logs:            pm2 logs serviceos
  Restart after code changes:
    npm run build && pm2 restart serviceos

  Run this installer again any time to change the port, switch database
  mode (fresh/reuse/restore a dump), or rebuild after pulling updates.

  Optional -- start pm2 automatically on server reboot:
    pm2 startup
    (follow the one-line sudo command it prints, then: pm2 save)
EOF
