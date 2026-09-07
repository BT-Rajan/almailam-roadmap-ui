-- Migration 0070: client-facing email OTP approval for contracts.
--
-- Adds the same four otp_code_hash/otp_expires_at/otp_attempts/
-- otp_sent_at columns migrations 0066/0067/0068 added to
-- `clients`/`projects`/`quotations` (see EmailOtpMixin in
-- app/models/mixins.py) -- a contract now moves to "Signed" only via a
-- confirmed email OTP (see contract_service.send_contract_otp/
-- verify_contract_otp), not a bare status change.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0070_contract_otp.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'otp_code_hash'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE contracts
     ADD COLUMN otp_code_hash VARCHAR(255) NULL AFTER finalized_at,
     ADD COLUMN otp_expires_at DATETIME NULL AFTER otp_code_hash,
     ADD COLUMN otp_attempts SMALLINT NOT NULL DEFAULT 0 AFTER otp_expires_at,
     ADD COLUMN otp_sent_at DATETIME NULL AFTER otp_attempts',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0070 complete.' AS status;
