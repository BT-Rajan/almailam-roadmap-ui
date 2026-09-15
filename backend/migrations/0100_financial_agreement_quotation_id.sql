-- Migration 0100: financial_agreements.quotation_id
--
-- A Payment Plan (financial_agreements row) has only ever recorded its
-- source quotation as free text (quotation_reference, VARCHAR(30),
-- unvalidated, user-typed) -- not a real link. This adds a proper FK,
-- mirroring contracts.quotation_id (migration 0033): resolved and set
-- server-side at creation from the project's Approved quotation (see
-- payment_service.create_agreement), never user-editable, so it stays
-- a fixed, trustworthy reference for the life of the agreement instead
-- of a string that could drift or never have been filled in correctly.
--
-- quotation_reference/contract_reference are left in place (nothing
-- reads them for this purpose anymore, but dropping columns outright
-- is a separate, riskier cleanup this migration doesn't attempt).
--
-- Idempotent -- safe to re-run. Run against your MySQL/MariaDB database:
--   mysql -u <user> -p <database> < backend/migrations/0100_financial_agreement_quotation_id.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements' AND COLUMN_NAME = 'quotation_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE financial_agreements ADD COLUMN quotation_id BIGINT UNSIGNED NULL AFTER project_id',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements' AND CONSTRAINT_NAME = 'fk_financial_agreements_quotation'
);
SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE financial_agreements ADD CONSTRAINT fk_financial_agreements_quotation FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE RESTRICT',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements' AND INDEX_NAME = 'idx_financial_agreements_quotation'
);
SET @sql = IF(@idx_exists = 0,
  'ALTER TABLE financial_agreements ADD INDEX idx_financial_agreements_quotation (quotation_id)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill: an existing agreement's quotation_reference is free text
-- but, in practice, was always seeded from the project's Approved
-- quotation's own quotation_no (see PaymentPlanFormPage.vue) -- so a
-- direct string match against quotations.quotation_no recovers the
-- real link for every agreement where staff didn't overwrite it.
-- Anything left NULL after this (reference blank, edited away, or
-- never matched a real quotation) stays NULL rather than guessed at --
-- see payment_service.create_agreement for how every *new* agreement
-- gets this set correctly and unambiguously going forward.
UPDATE financial_agreements fa
JOIN quotations q ON q.quotation_no = fa.quotation_reference AND q.project_id = fa.project_id
SET fa.quotation_id = q.id
WHERE fa.quotation_id IS NULL AND fa.quotation_reference IS NOT NULL;

SELECT 'Migration 0100 complete.' AS status;
