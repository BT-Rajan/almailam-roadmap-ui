#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================================
# ServiceOS -- reset a database to a clean backend/schema.sql
#
# backend/schema.sql is the single, complete definition of the database
# (there are no migration patches). install.sh loads it automatically
# only into an EMPTY database, on first deployment, and never modifies an
# existing one. Use this script when an existing database must be rebuilt
# to the current schema.sql, e.g. after schema.sql changed. It:
#
#   1. Drops every existing table in the target database (DESTROYS ALL DATA)
#   2. Loads backend/schema.sql fresh
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
from backend/schema.sql. DESTROYS ALL DATA in that database. Run
./install.sh afterwards to install deps and (re)start the app.

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

# --no-defaults first: ignore ~/.my.cnf etc. A [client] `force` option
# there makes the client exit 0 after a failed statement, so a broken
# schema load would look successful (see install.sh's db_run).
run_sql() {
    "$DB_CLIENT" --no-defaults --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "$DB_NAME"
}

run_sql_n() {
    "$DB_CLIENT" --no-defaults --protocol=tcp -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -N -s "$DB_NAME"
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

unset MYSQL_PWD

log "Database reset complete"

cat <<EOF

Next step:
  cd $INSTANCE_DIR
  ./install.sh --instance=$INSTANCE

The database now holds exactly backend/schema.sql and no data.
install.sh recreates the admin user and restarts the app.

EOF
