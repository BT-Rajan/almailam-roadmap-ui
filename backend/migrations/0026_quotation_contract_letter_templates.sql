-- Migration 0026: lettered quotation/contract templates
--
-- Adds the fields needed to render a quotation or contract into one of
-- a fixed set of pre-written letters (verbatim wording/layout, app data
-- merged in) instead of the original generic itemised-pricing layout.
-- template_key stays NULL on every existing row, so nothing already in
-- the database changes behaviour -- the generic layout keeps rendering
-- exactly as before wherever template_key is unset.
--
-- Idempotent -- every ADD COLUMN is guarded by an information_schema
-- check, same pattern as earlier migrations. Safe to re-run.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0026_quotation_contract_letter_templates.sql

-- --- quotations -------------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'template_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN template_key VARCHAR(40) NULL AFTER amount',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'client_representative'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN client_representative VARCHAR(150) NULL AFTER template_key',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'subject_line'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN subject_line VARCHAR(300) NULL AFTER client_representative',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'project_reference'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN project_reference VARCHAR(300) NULL AFTER subject_line',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'fee_frequency'
);
SET @sql = IF(@col_exists = 0,
  "ALTER TABLE quotations ADD COLUMN fee_frequency ENUM('Lump Sum','Monthly') NOT NULL DEFAULT 'Lump Sum' AFTER project_reference",
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'scope_items'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN scope_items JSON NULL AFTER fee_frequency',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'payment_terms'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN payment_terms JSON NULL AFTER scope_items',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'finalized_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations ADD COLUMN finalized_at DATETIME NULL AFTER payment_terms',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Existing rows get an empty list rather than NULL for the two JSON
-- columns, matching the ORM's `default=list` and keeping reads simple
-- (no NULL-vs-empty-array branching in application code).
UPDATE quotations SET scope_items = JSON_ARRAY() WHERE scope_items IS NULL;
UPDATE quotations SET payment_terms = JSON_ARRAY() WHERE payment_terms IS NULL;
ALTER TABLE quotations MODIFY COLUMN scope_items JSON NOT NULL;
ALTER TABLE quotations MODIFY COLUMN payment_terms JSON NOT NULL;

-- --- contracts ----------------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'template_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN template_key VARCHAR(40) NULL AFTER scope_summary',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'is_bilingual'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN is_bilingual TINYINT(1) NOT NULL DEFAULT 0 AFTER template_key',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'subject_line_ar'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN subject_line_ar VARCHAR(300) NULL AFTER is_bilingual',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'subject_line_en'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN subject_line_en VARCHAR(300) NULL AFTER subject_line_ar',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'project_reference'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN project_reference VARCHAR(300) NULL AFTER subject_line_en',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'fee_frequency'
);
SET @sql = IF(@col_exists = 0,
  "ALTER TABLE contracts ADD COLUMN fee_frequency ENUM('Lump Sum','Monthly') NOT NULL DEFAULT 'Lump Sum' AFTER project_reference",
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'scope_items_ar'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN scope_items_ar JSON NULL AFTER fee_frequency',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'scope_items_en'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN scope_items_en JSON NULL AFTER scope_items_ar',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'payment_terms_ar'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN payment_terms_ar JSON NULL AFTER scope_items_en',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'payment_terms_en'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN payment_terms_en JSON NULL AFTER payment_terms_ar',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'finalized_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN finalized_at DATETIME NULL AFTER payment_terms_en',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE contracts SET scope_items_ar = JSON_ARRAY() WHERE scope_items_ar IS NULL;
UPDATE contracts SET scope_items_en = JSON_ARRAY() WHERE scope_items_en IS NULL;
UPDATE contracts SET payment_terms_ar = JSON_ARRAY() WHERE payment_terms_ar IS NULL;
UPDATE contracts SET payment_terms_en = JSON_ARRAY() WHERE payment_terms_en IS NULL;
ALTER TABLE contracts MODIFY COLUMN scope_items_ar JSON NOT NULL;
ALTER TABLE contracts MODIFY COLUMN scope_items_en JSON NOT NULL;
ALTER TABLE contracts MODIFY COLUMN payment_terms_ar JSON NOT NULL;
ALTER TABLE contracts MODIFY COLUMN payment_terms_en JSON NOT NULL;

SELECT 'Migration 0026 complete.' AS status;
