-- Migration 0084: add pricing to Permits
--
-- Permits had no price at all until now -- the catalog explicitly modeled
-- "a permit is picked as a whole, not broken into priced sub-items" with
-- no cost field, so the Scope summary and quotations had nothing to show
-- for them (unlike Design/Supervision, which have always been priced).
-- This adds a standard fixed fee per permit catalog item (same one-time
-- shape as ServiceCatalogActivity.fixed_cost), plus a snapshot column on
-- ProjectSelectedPermit that captures that price at selection time, same
-- convention as permit_name.
--
-- Idempotent -- guarded by information_schema checks, same convention as
-- every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0084_permit_pricing.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'permit_catalog_items' AND column_name = 'fixed_cost'
);
SET @sql := IF(
    @col_exists = 0,
    'ALTER TABLE permit_catalog_items ADD COLUMN fixed_cost DECIMAL(12,2) NOT NULL DEFAULT 0',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_permits' AND column_name = 'permit_price'
);
SET @sql := IF(
    @col_exists = 0,
    'ALTER TABLE project_selected_permits ADD COLUMN permit_price DECIMAL(12,2) NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0084 complete.' AS status;
