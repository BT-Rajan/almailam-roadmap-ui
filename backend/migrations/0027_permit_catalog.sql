-- Migration 0027: configurable permit catalog
--
-- Replaces the free-text permit search (sourced from the government form
-- library) in the New Project Wizard with an admin-configurable catalog,
-- same pattern as migration 0009's service catalog. Flat -- no
-- activities sub-level, since a permit is picked as a whole.
--
-- Idempotent -- CREATE TABLE IF NOT EXISTS is naturally safe to re-run.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0027_permit_catalog.sql

CREATE TABLE IF NOT EXISTS permit_catalog_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    INDEX idx_permit_catalog_items_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0027 complete.' AS status;
