-- Migration 0033: quotation/contract workflow guardrails
--
-- Backs three workflow rules now enforced in quotation_service.py /
-- contract_service.py:
--   1. A contract must be generated from a specific quotation that is
--      already 'Approved' and finalized ("Final") -- adds
--      contracts.quotation_id to record that link.
--   2. Every quotation save writes a revision history row, the same
--      way contracts already do via contract_revisions -- adds the
--      new quotation_revisions table.
--
-- Idempotent -- safe to re-run. Run against your MySQL/MariaDB database:
--   mysql -u <user> -p <database> < backend/migrations/0033_quotation_contract_workflow_guardrails.sql

-- --- contracts.quotation_id --------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'quotation_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts ADD COLUMN quotation_id BIGINT UNSIGNED NULL AFTER project_id',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND CONSTRAINT_NAME = 'fk_contracts_quotation'
);
SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE contracts ADD CONSTRAINT fk_contracts_quotation FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE RESTRICT',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND INDEX_NAME = 'idx_contracts_quotation'
);
SET @sql = IF(@idx_exists = 0,
  'ALTER TABLE contracts ADD INDEX idx_contracts_quotation (quotation_id)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- quotation_revisions -------------------------------------------------

CREATE TABLE IF NOT EXISTS quotation_revisions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    quotation_id    BIGINT UNSIGNED NOT NULL,
    revision        VARCHAR(10) NOT NULL,
    revised_at      DATE NOT NULL,
    changed_by      BIGINT UNSIGNED NOT NULL,
    summary         TEXT NOT NULL,
    CONSTRAINT fk_quotation_revisions_quotation FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE,
    CONSTRAINT fk_quotation_revisions_user FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_quotation_revisions_quotation (quotation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Backfill: give every existing quotation an initial R0 revision row so
-- the revision history panel isn't empty for quotations created before
-- this migration. Uses each quotation's own prepared_by/created_at.
INSERT INTO quotation_revisions (quotation_id, revision, revised_at, changed_by, summary)
SELECT q.id, q.revision, DATE(q.created_at), q.prepared_by, 'Initial quotation created'
FROM quotations q
WHERE NOT EXISTS (
  SELECT 1 FROM quotation_revisions qr WHERE qr.quotation_id = q.id
);
