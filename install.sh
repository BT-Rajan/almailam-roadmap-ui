#!/usr/bin/env bash
#
# install.sh — One-shot dev environment setup for almailam-roadmap-ui on Ubuntu.
#
# Sets up:
#   - System packages (Python, MySQL, build tools)
#   - Node.js via nvm (if not already installed)
#   - MySQL database + schema (+ optional test data)
#   - Backend virtualenv + dependencies + .env
#   - Frontend npm dependencies
#   - Admin user (quick-start)
#
# Usage:
#   ./install.sh                # full install, prompts for MySQL root password
#   ./install.sh --with-testdata  # also loads backend/testdata.sql
#   ./install.sh --skip-db      # skip DB creation/schema import (already set up)
#
# After it finishes, start the app with:
#   Terminal 1: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload
#   Terminal 2: npm run dev
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Config / flags
# ---------------------------------------------------------------------------
WITH_TESTDATA=false
SKIP_DB=false
DB_NAME="almailam"
NODE_VERSION="20"

for arg in "$@"; do
  case "$arg" in
    --with-testdata) WITH_TESTDATA=true ;;
    --skip-db) SKIP_DB=true ;;
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$1"; }
err()  { printf '\033[1;31mERROR: %s\033[0m\n' "$1" >&2; }

require_cmd() { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
log "Installing system packages (git, python3, mysql-server, build tools)"
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip build-essential \
  curl mysql-server

# ---------------------------------------------------------------------------
# 2. Node.js via nvm
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

# ---------------------------------------------------------------------------
# 3. MySQL database + schema
# ---------------------------------------------------------------------------
if [ "$SKIP_DB" = false ]; then
  log "Setting up MySQL database '${DB_NAME}'"
  sudo systemctl enable --now mysql

  read -rsp "MySQL root password (blank if none set yet): " MYSQL_PWD_INPUT
  echo
  if [ -n "$MYSQL_PWD_INPUT" ]; then
    MYSQL_AUTH=(-u root -p"$MYSQL_PWD_INPUT")
  else
    MYSQL_AUTH=(-u root)
  fi

  sudo mysql "${MYSQL_AUTH[@]}" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARSET=utf8mb4;"
  sudo mysql "${MYSQL_AUTH[@]}" "${DB_NAME}" < backend/schema.sql

  if [ "$WITH_TESTDATA" = true ]; then
    log "Loading test data"
    sudo mysql "${MYSQL_AUTH[@]}" "${DB_NAME}" < backend/testdata.sql
  fi
else
  warn "Skipping DB setup (--skip-db passed)"
  MYSQL_PWD_INPUT=""
fi

# ---------------------------------------------------------------------------
# 4. Backend: venv + deps + .env
# ---------------------------------------------------------------------------
log "Setting up backend virtualenv"
cd backend
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  log "Creating backend/.env from .env.example"
  cp .env.example .env
  if [ -n "${MYSQL_PWD_INPUT:-}" ]; then
    sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=${MYSQL_PWD_INPUT}/" .env
  fi
  JWT_SECRET="$(openssl rand -hex 32)"
  sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${JWT_SECRET}/" .env
  warn "backend/.env created with a generated JWT secret. Add ANTHROPIC_API_KEY / DEEPSEEK_API_KEY yourself to enable AI features."
else
  warn "backend/.env already exists — leaving it untouched."
fi

log "Creating admin user (admin / Admin#99) if not already present"
python -m scripts.create_admin --quick-start || warn "Admin user step failed or already exists — check output above."

deactivate
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# 5. Frontend: npm install
# ---------------------------------------------------------------------------
log "Installing frontend dependencies"
export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && nvm use "$NODE_VERSION" >/dev/null 2>&1 || true
npm install

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
log "Setup complete!"
cat <<'EOF'

Start the app with two terminals:

  Terminal 1 (backend):
    cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload

  Terminal 2 (frontend):
    npm run dev

Then open http://localhost:5173 and log in with admin / Admin#99.
Backend health check: curl http://localhost:8000/api/health
EOF
