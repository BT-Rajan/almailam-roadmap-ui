-- Migration 0101: financial_agreements.contract_id
--
-- Payment Plan's contract_reference (free text, VARCHAR(30)) was meant
-- to record the contract eventually generated from this agreement --
-- but Payment Plan is always created *before* Contract in the project
-- workflow, so there was never actually a contract to reference at
-- that point, and _assert_agreement_editable refuses any edit to the
-- agreement once a contract exists on the project. The column was
-- therefore structurally dead: never exposed in the create/edit form,
-- and impossible to correctly fill in after the fact either.
--
-- This adds a real FK instead, written back server-side once the
-- contract actually exists (see contract_service.create_contract),
-- mirroring quotation_id (migration 0100) but in the other direction:
-- Contract -> Payment Plan instead of Payment Plan -> Quotation.
--
-- Idempotent -- safe to re-run. Run against your MySQL/MariaDB database:
--   mysql -u <user> -p <database> < backend/migrations/0101_financial_agreement_contract_id.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements' AND COLUMN_NAME = 'contract_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE financial_agreements ADD COLUMN contract_id BIGINT UNSIGNED NULL AFTER quotation_id',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements' AND CONSTRAINT_NAME = 'fk_financial_agreements_contract'
);
SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE financial_agreements ADD CONSTRAINT fk_financial_agreements_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE RESTRICT',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements' AND INDEX_NAME = 'idx_financial_agreements_contract'
);
SET @sql = IF(@idx_exists = 0,
  'ALTER TABLE financial_agreements ADD INDEX idx_financial_agreements_contract (contract_id)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill: link every existing agreement to its project's contract,
-- for projects that already have exactly one (the overwhelmingly
-- common case -- one contract per project in practice). Skips any
-- project with more than one contract row (e.g. a revised/replaced
-- one) rather than guessing which is the "real" one; those stay NULL,
-- same as any agreement with no contract yet.
UPDATE financial_agreements fa
JOIN (
  SELECT project_id, MIN(id) AS contract_id
  FROM contracts
  WHERE deleted_at IS NULL
  GROUP BY project_id
  HAVING COUNT(*) = 1
) c ON c.project_id = fa.project_id
SET fa.contract_id = c.contract_id
WHERE fa.contract_id IS NULL;

SELECT 'Migration 0101 complete.' AS status;
