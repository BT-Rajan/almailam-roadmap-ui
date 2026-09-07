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

# vue-i18n/@intlify (added with the bilingual i18n work) require Node
# >= 22 -- an older pin here installs a Node that satisfies nothing
# but this check, and every `npm install` then prints EBADENGINE
# warnings for every @intlify package. Track whatever the current
# dependencies actually need, not a version chosen when they didn't.
NODE_VERSION=22

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

    if ! git -C "$INSTANCE_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        die "$INSTANCE_DIR/.git exists but is not a valid git repository. Investigate/remove it manually, then re-run."
    fi

    # A directory may already exist here (pre-dating this script, or a
    # manual git init) without an 'origin' remote -- add/fix it rather
    # than failing, since REPO_URL is the one source of truth.
    if git -C "$INSTANCE_DIR" remote get-url origin >/dev/null 2>&1; then
        git -C "$INSTANCE_DIR" remote set-url origin "$REPO_URL"
    else
        log "No 'origin' remote in $INSTANCE_DIR -- adding it"
        git -C "$INSTANCE_DIR" remote add origin "$REPO_URL"
    fi

    git -C "$INSTANCE_DIR" fetch origin "$BRANCH"
    git -C "$INSTANCE_DIR" checkout "$BRANCH"
    git -C "$INSTANCE_DIR" reset --hard "origin/$BRANCH"
    # -fd only, no -x: respects .gitignore, so backend/.env, venv/,
    # node_modules, dist/ and ecosystem*.config.cjs are left alone.
    git -C "$INSTANCE_DIR" clean -fd
fi

# Printed both here and in the final summary -- when "I redeployed but
# don't see my change" gets reported, this is the one line that tells
# you whether the checkout genuinely moved (compare against `git log`
# on your own clone) before looking anywhere else, e.g. at a stale pm2
# process or a browser cache still holding the old bundle.
DEPLOYED_COMMIT="$(git -C "$INSTANCE_DIR" rev-parse --short HEAD)"
log "Deployed commit: $DEPLOYED_COMMIT ($(git -C "$INSTANCE_DIR" log -1 --format=%s))"

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

# --no-defaults MUST come first (the client requires it as the very
# first option) and makes the client ignore every option file
# (~/.my.cnf, /etc/mysql/my.cnf, etc.) entirely. This isn't
# precautionary: verified live against this exact client that a
# [client] `force` setting in ~/.my.cnf -- invisible to and
# uncontrollable by this script -- makes it exit 0 even after a
# statement fails, and any later statements in the same file still
# silently run, so the migration "succeeds" while part of it never
# happened. --no-defaults removes the setting from consideration
# altogether rather than trying to detect its effects afterward, which
# doesn't reliably work: the schema_migrations INSERT is a separate,
# unaffected db_run call, so a filename can end up recorded as applied
# even though the file's own statements partly failed. Every
# connection parameter this script needs is already passed explicitly
# on the command line, so no option file was ever required here.
db_run() {
    "$DB_CLIENT" --no-defaults --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME"
}

db_query() {
    "$DB_CLIENT" --no-defaults --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -N -s "$DB_NAME"
}

MIGRATIONS_APPLIED_THIS_RUN=0
MIGRATIONS_SKIPPED_ALREADY_APPLIED=0
# Declared upfront (rather than only inside the branch below) so the
# final summary can always reference ${#MIGRATIONS[@]} even when there
# is no migrations directory at all -- set -u would otherwise treat an
# array that was never assigned in that branch as an unbound variable.
MIGRATIONS=()

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

        log "Applying database migrations (${#MIGRATIONS[@]} file(s) on disk)"

        # Tracks which migration files have already been run against this
        # database, so re-running install.sh skips them instead of
        # replaying every .sql file from scratch every time. Each
        # migration is still written to be idempotent on its own
        # (information_schema-guarded ADD COLUMN, etc.) -- this table is a
        # second, cheaper line of defense: skip the whole file rather than
        # rely on every statement inside it tolerating a second run.
        if ! echo "
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename VARCHAR(255) NOT NULL PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            " | db_run; then
            die "Could not create/verify the schema_migrations table. See the database error above."
        fi

        for migration in "${MIGRATIONS[@]}"; do

            migration_name="$(basename "$migration")"

            already_applied="$(
                echo "SELECT COUNT(*) FROM schema_migrations WHERE filename = '$migration_name';" |
                    db_query
            )"

            if [[ "$already_applied" != "0" ]]; then
                log "Migration: $migration_name (already applied, skipping)"
                MIGRATIONS_SKIPPED_ALREADY_APPLIED=$((MIGRATIONS_SKIPPED_ALREADY_APPLIED + 1))
                continue
            fi

            log "Migration: $migration_name"

            # Explicit if/die instead of relying on bare `set -e` to abort
            # the script here: this way a failure names the exact file
            # that broke and says plainly that nothing after it ran,
            # instead of the operator having to infer that from wherever
            # the script happened to stop. schema_migrations is only
            # written to on success (below), so a failed file is never
            # recorded as applied -- re-running install.sh after fixing
            # the underlying issue retries it and everything after it,
            # not just the one file.
            if ! db_run < "$migration"; then
                die "Migration '$migration_name' failed (see the database error above). No later migrations were applied. Fix the issue and re-run this installer -- already-applied migrations are skipped automatically, so it's safe to re-run from here."
            fi

            if ! echo "INSERT INTO schema_migrations (filename) VALUES ('$migration_name');" | db_run; then
                die "Migration '$migration_name' ran but recording it in schema_migrations failed. Re-running this installer would re-apply it -- check that the migration file is safe to run twice before doing so, or insert the schema_migrations row manually."
            fi

            MIGRATIONS_APPLIED_THIS_RUN=$((MIGRATIONS_APPLIED_THIS_RUN + 1))
        done

        log "All migrations completed ($MIGRATIONS_APPLIED_THIS_RUN applied this run, $MIGRATIONS_SKIPPED_ALREADY_APPLIED already applied)"

        # Reconciliation, independent of every exit code checked above:
        # ask the database itself which of the .sql files on disk it has
        # no record of, rather than trusting that "the loop completed" or
        # "the client returned 0" actually means every file's statements
        # landed. db_run's --no-defaults already closes the specific
        # ~/.my.cnf `force` risk this was originally added to catch (see
        # the comment on db_run above), but this stays as a second,
        # independent line of defense -- e.g. a process killed between a
        # migration's own db_run and the schema_migrations INSERT that
        # records it, or any future change to this script that
        # reintroduces a path where a file's statements could land
        # without ever getting recorded. Cheap, and checks something
        # neither of those exit codes alone can guarantee: that the
        # database's own bookkeeping actually matches disk.
        # Captured via a plain command substitution, not
        # `mapfile ... < <(...)` -- a failing query inside process
        # substitution doesn't propagate its exit code back to this
        # script even under `set -e`, so a transient failure here would
        # silently read as "recorded nothing", which would then make
        # every migration look falsely missing below. $(...) surfaces
        # that failure directly instead.
        if ! RECORDED_MIGRATIONS_RAW="$(echo "SELECT filename FROM schema_migrations;" | db_query)"; then
            die "Could not read back schema_migrations to verify which migrations actually applied. See the database error above."
        fi
        mapfile -t RECORDED_MIGRATIONS <<< "$RECORDED_MIGRATIONS_RAW"

        MISSING_MIGRATIONS=()
        for migration in "${MIGRATIONS[@]}"; do
            migration_name="$(basename "$migration")"
            found=false
            for recorded in "${RECORDED_MIGRATIONS[@]}"; do
                if [[ "$recorded" == "$migration_name" ]]; then
                    found=true
                    break
                fi
            done
            [[ "$found" == true ]] || MISSING_MIGRATIONS+=("$migration_name")
        done

        if (( ${#MISSING_MIGRATIONS[@]} > 0 )); then
            die "Migrations exist on disk but are NOT recorded as applied in schema_migrations, even though the loop above reported success: ${MISSING_MIGRATIONS[*]}. This means the database silently didn't run what this script asked it to (a ~/.my.cnf 'force' setting is the most likely cause) -- investigate before continuing; the app is not safe to serve in this state."
        fi

        log "Verified: all ${#MIGRATIONS[@]} migration file(s) on disk are recorded as applied in schema_migrations"

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

    # npm run build exiting 0 is not, by itself, proof the site is
    # actually servable -- a plugin/build step that fails partway
    # through without propagating a non-zero exit is rare but has
    # happened in this ecosystem, and it's cheap to rule out here
    # rather than have it surface later as "the page is blank" with no
    # clue why. The backend's own catch-all route (see app/main.py)
    # serves dist/index.html for every non-API path, so its absence is
    # exactly what would make the whole site 404/500.
    if [[ ! -f "$INSTANCE_DIR/dist/index.html" ]]; then
        die "npm run build reported success but $INSTANCE_DIR/dist/index.html is missing. The frontend build did not actually produce a servable site -- check the build output above."
    fi
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
            // Runs the local vite binary directly rather than through
            // "npm run dev" -- npm run scripts spawn vite as a *child*
            // process, and npm doesn't reliably forward the SIGTERM pm2
            // sends on 'pm2 delete'/'pm2 restart' down to that child
            // (a long-standing Node ecosystem gotcha). That can leave
            // the actual vite dev server still bound to this port and
            // still serving the *old* code after a redeploy, even
            // though pm2 believes it started a fresh process -- the
            // exact "reran install.sh but the fix isn't showing up"
            // symptom this is fixing. Running vite itself as pm2's
            // managed process means pm2's kill signal goes straight to
            // the process actually holding the port.
            script: "${INSTANCE_DIR}/node_modules/.bin/vite",
            args: "--host 0.0.0.0 --port ${FRONTEND_PORT}",
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

    # Belt-and-suspenders on top of the pm2 delete above: a process that
    # ended up bound to these ports *outside* pm2's tracking (a manual
    # "npm run dev" from before this instance was ever pm2-managed, or a
    # previous run's orphaned vite child -- see the comment on
    # PM2_FRONTEND_NAME's script above) would otherwise keep silently
    # serving stale content on this port forever, with every future
    # 'pm2 start' none the wiser since it's not pm2's process to know
    # about. Best-effort only -- skipped with a warning if neither tool
    # is available, same as the ufw check below.
    if require_cmd fuser; then
        fuser -k "${BACKEND_PORT}/tcp" >/dev/null 2>&1 || true
        fuser -k "${FRONTEND_PORT}/tcp" >/dev/null 2>&1 || true
    elif require_cmd lsof; then
        lsof -ti "tcp:${BACKEND_PORT}" 2>/dev/null | xargs -r kill -9 || true
        lsof -ti "tcp:${FRONTEND_PORT}" 2>/dev/null | xargs -r kill -9 || true
    else
        warn "Neither fuser nor lsof found -- skipping the stale-process port check. If the redeployed app still shows old content, manually confirm nothing outside pm2 is still bound to ${BACKEND_PORT} or ${FRONTEND_PORT}."
    fi

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

Deployed commit:
  ${DEPLOYED_COMMIT}

Migrations:
  ${MIGRATIONS_APPLIED_THIS_RUN} applied this run, ${MIGRATIONS_SKIPPED_ALREADY_APPLIED} already applied, ${#MIGRATIONS[@]} total on disk -- verified against schema_migrations

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

Deployed commit:
  ${DEPLOYED_COMMIT}

Migrations:
  ${MIGRATIONS_APPLIED_THIS_RUN} applied this run, ${MIGRATIONS_SKIPPED_ALREADY_APPLIED} already applied, ${#MIGRATIONS[@]} total on disk -- verified against schema_migrations

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
