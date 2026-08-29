-- Migration 0055: widen rich-text content columns to MEDIUMTEXT
--
-- The Quotation/Contract preview editors now save formatted HTML (bold,
-- underline, font size, inline base64 images) instead of plain text for
-- these three fields. TEXT's 64KB cap is easily blown past by a single
-- embedded image, so widen to MEDIUMTEXT (16MB) -- matches the precedent
-- set by knowledge_qa_cache.answer_text (migration 0043).
--
-- terms_and_conditions is untouched -- it's a JSON column (still an
-- array of per-term HTML strings), and MySQL/MariaDB JSON columns are
-- already sized well past TEXT's limit.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0055_rich_text_content_widen.sql

SET @db := DATABASE();

SET @needs_widen := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'notes' AND data_type = 'text'
);
SET @sql := IF(@needs_widen > 0, 'ALTER TABLE quotations MODIFY COLUMN notes MEDIUMTEXT NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @needs_widen := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'scope_summary' AND data_type = 'text'
);
SET @sql := IF(@needs_widen > 0, 'ALTER TABLE contracts MODIFY COLUMN scope_summary MEDIUMTEXT NOT NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @needs_widen := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contract_clauses' AND column_name = 'content' AND data_type = 'text'
);
SET @sql := IF(@needs_widen > 0, 'ALTER TABLE contract_clauses MODIFY COLUMN content MEDIUMTEXT NOT NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0055 complete.' AS status;
