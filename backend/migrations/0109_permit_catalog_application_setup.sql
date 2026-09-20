-- Migration 0109: Configure each permit type once
--
-- A permit type (permit_catalog_items: "Baladia Permits", "KFD Permits")
-- now carries the setup its applications need, in one place:
--   authority_id        -- which authority the permit is filed with
--   form_id             -- which permit application form it uses
--   required_documents  -- optional checklist override (JSON array of
--                          names); NULL means "use the form's own list"
--
-- This is what lets a planned permit start its application with nothing
-- to choose, and ends the trap where a form with no service_tags is
-- offered for no project: a permit-driven application never goes
-- through the service-tag filter.
--
-- Seeds the two permit types from migration 0107's authorities/forms.
-- Non-destructive and idempotent: columns/constraints are guarded by
-- information_schema checks, and a permit type is only mapped while it
-- has no form yet, so an admin's own mapping is never overwritten.
--
-- Run: mysql -u <user> -p <database> < backend/migrations/0109_permit_catalog_application_setup.sql

SET NAMES utf8mb4;
SET @db := DATABASE();

-- 1. Columns
SET @has_col := (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'permit_catalog_items' AND column_name = 'authority_id');
SET @sql := IF(@has_col = 0,
    'ALTER TABLE permit_catalog_items ADD COLUMN authority_id BIGINT UNSIGNED NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'permit_catalog_items' AND column_name = 'form_id');
SET @sql := IF(@has_col = 0,
    'ALTER TABLE permit_catalog_items ADD COLUMN form_id BIGINT UNSIGNED NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'permit_catalog_items' AND column_name = 'required_documents');
SET @sql := IF(@has_col = 0,
    'ALTER TABLE permit_catalog_items ADD COLUMN required_documents JSON NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. Foreign keys (SET NULL: retiring an authority/form unmaps the permit
--    type instead of blocking or deleting it)
SET @has_fk := (SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE table_schema = @db AND table_name = 'permit_catalog_items'
      AND constraint_name = 'fk_permit_catalog_items_authority');
SET @sql := IF(@has_fk = 0,
    'ALTER TABLE permit_catalog_items ADD CONSTRAINT fk_permit_catalog_items_authority FOREIGN KEY (authority_id) REFERENCES government_authorities(id) ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_fk := (SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE table_schema = @db AND table_name = 'permit_catalog_items'
      AND constraint_name = 'fk_permit_catalog_items_form');
SET @sql := IF(@has_fk = 0,
    'ALTER TABLE permit_catalog_items ADD CONSTRAINT fk_permit_catalog_items_form FOREIGN KEY (form_id) REFERENCES government_forms(id) ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. Seed the two permit types with the forms 0107 created
UPDATE permit_catalog_items p
JOIN government_forms f ON f.form_code = 'BALADIA-PERMIT' AND f.deleted_at IS NULL
SET p.authority_id = f.authority_id, p.form_id = f.id
WHERE p.name = 'Baladia Permits' AND p.deleted_at IS NULL AND p.form_id IS NULL;

UPDATE permit_catalog_items p
JOIN government_forms f ON f.form_code = 'KFD-PERMIT' AND f.deleted_at IS NULL
SET p.authority_id = f.authority_id, p.form_id = f.id
WHERE p.name = 'KFD Permits' AND p.deleted_at IS NULL AND p.form_id IS NULL;

SELECT 'Migration 0109 complete.' AS status;
