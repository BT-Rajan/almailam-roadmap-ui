-- Migration 0094: remove otp_code_hash/otp_expires_at/otp_attempts/
-- otp_sent_at from clients, projects, quotations, and contracts.
--
-- These backed EmailOtpMixin (app/models/mixins.py) -- columns for the
-- old email-OTP read-back confirmation flow (client onboarding,
-- Requirement scope, Quotation approval, Contract signing, project
-- hand-over). Every one of those now confirms via a signed-document
-- upload instead (see quotation_service.confirm_quotation_approval and
-- its siblings in contract_service/project_service/client_service), so
-- nothing has written these columns for a while -- migration 0080
-- already removed the *_otp email templates that used to accompany
-- them. EmailOtpMixin itself, and the two remaining call sites that
-- still defensively cleared these columns back to NULL/0
-- (quotation_service.confirm_quotation_approval,
-- project_service.save_scope_of_work), are removed in the same change
-- as this migration -- so unlike the earlier "kept as inert columns"
-- decision, there is now truly nothing left anywhere that reads or
-- writes them.
--
-- Idempotent -- each DROP COLUMN is guarded by an information_schema
-- check, same convention as every other migration here (e.g. migration
-- 0054).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0094_remove_otp_columns.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'clients' AND column_name = 'otp_code_hash'
);
SET @sql := IF(@col_exists > 0,
    'ALTER TABLE clients DROP COLUMN otp_code_hash, DROP COLUMN otp_expires_at, DROP COLUMN otp_attempts, DROP COLUMN otp_sent_at',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'otp_code_hash'
);
SET @sql := IF(@col_exists > 0,
    'ALTER TABLE projects DROP COLUMN otp_code_hash, DROP COLUMN otp_expires_at, DROP COLUMN otp_attempts, DROP COLUMN otp_sent_at',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'otp_code_hash'
);
SET @sql := IF(@col_exists > 0,
    'ALTER TABLE quotations DROP COLUMN otp_code_hash, DROP COLUMN otp_expires_at, DROP COLUMN otp_attempts, DROP COLUMN otp_sent_at',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'otp_code_hash'
);
SET @sql := IF(@col_exists > 0,
    'ALTER TABLE contracts DROP COLUMN otp_code_hash, DROP COLUMN otp_expires_at, DROP COLUMN otp_attempts, DROP COLUMN otp_sent_at',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0094 complete.' AS status;
