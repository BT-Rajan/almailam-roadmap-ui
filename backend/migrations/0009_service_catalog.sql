-- Migration 0009: configurable service catalog
--
-- Replaces the hardcoded PROJECT_SERVICES list with an admin-configurable
-- catalog: any number of services (no duplicates, case-insensitive,
-- enforced in service_catalog_service.py rather than a DB-level unique
-- constraint so a soft-deleted service's name can be reused later),
-- each with any number of activities (sub-services), each activity
-- carrying its own fixed cost.
--
-- Idempotent -- CREATE TABLE IF NOT EXISTS is naturally safe to re-run,
-- same pattern as earlier migrations.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0009_service_catalog.sql

CREATE TABLE IF NOT EXISTS service_catalog_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    INDEX idx_service_catalog_items_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS service_catalog_activities (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    service_id      BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(150) NOT NULL,
    fixed_cost      DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_service_catalog_activities_service
        FOREIGN KEY (service_id) REFERENCES service_catalog_items(id) ON DELETE CASCADE,
    INDEX idx_service_catalog_activities_service (service_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed from the previous hardcoded PROJECT_SERVICES list so existing
-- projects' `service` values still match something in the new catalog
-- after this migration runs -- guarded so it only seeds an empty table,
-- same backfill-guard pattern as migrations 0006/0007.
INSERT INTO service_catalog_items (name)
SELECT * FROM (
    SELECT 'Structural Engineering' AS name
    UNION ALL SELECT 'MEP Design'
    UNION ALL SELECT 'Architectural Design'
    UNION ALL SELECT 'Fire & Safety Engineering'
    UNION ALL SELECT 'Civil Engineering'
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM service_catalog_items);

SELECT 'Migration 0009 complete.' AS status;
