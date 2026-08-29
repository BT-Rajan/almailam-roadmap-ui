-- Migration 0054: remove Contract.template_name
--
-- Mirrors how Quotation has never had a free-text "template name" of
-- its own -- a quotation is identified purely by quotation_no +
-- revision, and a contract should be too now that the New Contract
-- dialog no longer asks for one.
--
-- Idempotent -- guarded by an information_schema check, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0054_remove_contract_template_name.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'template_name'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN template_name', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0054 complete.' AS status;
