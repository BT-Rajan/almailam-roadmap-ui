#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS -- one-time DB reset from schema.sql
#
# Use this ONCE when a database's migration history has gotten out of sync
# (or you just want a clean slate) instead of replaying all
# backend/migrations/*.sql files one by one. schema.sql is the up-to-date,
# fully-collapsed shape of the database (it already includes everything
# through the latest migration), so this script:
#
#   1. Drops every existing table in the target database (DESTROYS ALL DATA)
#   2. Loads backend/schema.sql fresh
#   3. Creates schema_migrations and inserts one row per file currently in
#      backend/migrations/, so a subsequent ./install.sh run sees every
#      migration as "already applied" and does not try to replay any of
#      them against the fresh schema
#
# It does NOT touch backend/.env, does NOT install dependencies, does NOT
# start pm2 -- run ./install.sh afterwards for all of that, same as normal.
#
# Usage:
#   ./reset_db_from_schema.sh --instance=dev
#   ./reset_db_from_schema.sh --instance=test
#   ./reset_db_from_schema.sh --instance=dev --yes     (skip confirmation)
# ============================================================================

APPS_DIR="/apps"

INSTANCE=""
ASSUME_YES=false

for arg in "$@"; do
    case "$arg" in
        --instance=dev)  INSTANCE="dev" ;;
        --instance=test) INSTANCE="test" ;;
        --yes|-y)        ASSUME_YES=true ;;
        -h|--help)
            cat <<EOF

Usage:
  ./reset_db_from_schema.sh --instance=dev|test [--yes]

Drops every table in the instance's configured database and reloads it
from backend/schema.sql, then marks all backend/migrations/*.sql files as
already applied. Run ./install.sh afterwards to install deps and start
the app -- it will see the migrations table fully populated and skip
straight past them.

EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option: $arg" >&2
            exit 1
            ;;
    esac
done

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$1"; }
err()  { printf '\033[1;31mERROR: %s\033[0m\n' "$1" >&2; }
die()  { err "$1"; exit 1; }
require_cmd() { command -v "$1" >/dev/null 2>&1; }

if [[ -z "$INSTANCE" ]]; then
    if [[ "$ASSUME_YES" == true ]]; then
        die "Non-interactive mode requires --instance=dev or --instance=test"
    fi
    echo
    echo "Which instance's database do you want to reset?"
    echo "  dev   -> /apps/serviceos"
    echo "  test  -> /apps/alhadi-test"
    read -r -p "Select [dev/test]: " answer || true
    case "$answer" in
        dev|Dev|DEV)   INSTANCE="dev" ;;
        test|Test|TEST) INSTANCE="test" ;;
        *) die "Invalid selection: '$answer' (expected 'dev' or 'test')" ;;
    esac
fi

case "$INSTANCE" in
    dev)  INSTANCE_NAME="serviceos" ;;
    test) INSTANCE_NAME="alhadi-test" ;;
    *) die "Invalid instance: $INSTANCE (expected 'dev' or 'test')" ;;
esac

INSTANCE_DIR="$APPS_DIR/$INSTANCE_NAME"
BACKEND_DIR="$INSTANCE_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
SCHEMA_FILE="$BACKEND_DIR/schema.sql"
MIGRATIONS_DIR="$BACKEND_DIR/migrations"

log "Instance: $INSTANCE -> $INSTANCE_DIR"

[[ -f "$ENV_FILE" ]]    || die "$ENV_FILE not found."
[[ -f "$SCHEMA_FILE" ]] || die "$SCHEMA_FILE not found."

get_env() {
    local key="$1" default="${2:-}" value=""
    value="$(sed -n -e "s/^${key}=//p" "$ENV_FILE" | head -n 1)"
    value="${value%$'\r'}"
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
        value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
        value="${value:1:${#value}-2}"
    fi
    echo "${value:-$default}"
}

DB_HOST="$(get_env DB_HOST "localhost")"
DB_PORT="$(get_env DB_PORT "3306")"
DB_NAME="$(get_env DB_NAME "")"
DB_USER="$(get_env DB_USER "app_user")"
DB_PASSWORD="$(get_env DB_PASSWORD "")"

[[ -n "$DB_NAME" ]] || die "DB_NAME is not set in $ENV_FILE."

if require_cmd mariadb; then
    DB_CLIENT="mariadb"
elif require_cmd mysql; then
    DB_CLIENT="mysql"
else
    die "Neither mysql nor mariadb client is installed."
fi

export MYSQL_PWD="$DB_PASSWORD"

run_sql() {
    "$DB_CLIENT" --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME"
}

run_sql_n() {
    "$DB_CLIENT" --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -N -s "$DB_NAME"
}

log "Testing database connection"
echo "SELECT 1;" | run_sql >/dev/null 2>&1 || { unset MYSQL_PWD; die "Cannot connect to database '$DB_NAME' as ${DB_USER}@${DB_HOST}:${DB_PORT}."; }
log "Connected to $DB_NAME @ ${DB_HOST}:${DB_PORT}"

# ----------------------------------------------------------------------------
# Confirm -- this is destructive
# ----------------------------------------------------------------------------

TABLE_COUNT="$(echo "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DB_NAME';" | run_sql_n)"

warn "This will DROP ALL $TABLE_COUNT existing tables in '$DB_NAME' on ${DB_HOST}:${DB_PORT} and reload them from schema.sql."
warn "All existing data will be permanently lost. There is no undo."

if [[ "$ASSUME_YES" != true ]]; then
    read -r -p "Type the database name ('$DB_NAME') to confirm: " confirm || true
    [[ "$confirm" == "$DB_NAME" ]] || die "Confirmation did not match '$DB_NAME'. Aborting -- nothing was touched."
fi

# ----------------------------------------------------------------------------
# 1. Drop every existing table
# ----------------------------------------------------------------------------

log "Dropping all existing tables in $DB_NAME"

DROP_SQL="$(
    echo "SELECT CONCAT('DROP TABLE IF EXISTS \`', table_name, '\`;') FROM information_schema.tables WHERE table_schema = '$DB_NAME';" | run_sql_n
)"

{
    echo "SET FOREIGN_KEY_CHECKS = 0;"
    echo "$DROP_SQL"
    echo "SET FOREIGN_KEY_CHECKS = 1;"
} | run_sql

log "All tables dropped"

# ----------------------------------------------------------------------------
# 2. Load schema.sql fresh
# ----------------------------------------------------------------------------

log "Loading schema.sql"
run_sql < "$SCHEMA_FILE"
log "Schema loaded"

# ----------------------------------------------------------------------------
# 3. Mark every migration file as already applied
# ----------------------------------------------------------------------------

log "Recording migration history (schema.sql already reflects all of these)"

echo "
    CREATE TABLE IF NOT EXISTS schema_migrations (
        filename VARCHAR(255) NOT NULL PRIMARY KEY,
        applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
" | run_sql

if [[ -d "$MIGRATIONS_DIR" ]]; then
    mapfile -t MIGRATIONS < <(find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name '*.sql' -printf '%f\n' | sort)

    if (( ${#MIGRATIONS[@]} > 0 )); then
        {
            for m in "${MIGRATIONS[@]}"; do
                echo "INSERT IGNORE INTO schema_migrations (filename) VALUES ('$m');"
            done
        } | run_sql
        log "Recorded ${#MIGRATIONS[@]} migrations as applied"
    else
        warn "No migration files found under $MIGRATIONS_DIR"
    fi
else
    warn "No migrations directory found at $MIGRATIONS_DIR"
fi

unset MYSQL_PWD

log "Database reset complete"

cat <<EOF

Next step:
  cd $INSTANCE_DIR
  ./install.sh --instance=$INSTANCE

install.sh will see every migration already recorded in schema_migrations
and skip straight to the admin-user check, dependency install, and pm2
(re)start.

EOF
