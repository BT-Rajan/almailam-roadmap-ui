-- Migration 0068: client-facing email OTP approval for quotations.
--
-- Adds the same four otp_code_hash/otp_expires_at/otp_attempts/
-- otp_sent_at columns migrations 0066/0067 added to `clients`/`projects`
-- (see EmailOtpMixin in app/models/mixins.py) -- a quotation now moves
-- to "Approved" only via a confirmed email OTP (see quotation_service.
-- send_quotation_otp/verify_quotation_otp), not a bare status change.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0068_quotation_otp.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'otp_code_hash'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE quotations
     ADD COLUMN otp_code_hash VARCHAR(255) NULL AFTER finalized_at,
     ADD COLUMN otp_expires_at DATETIME NULL AFTER otp_code_hash,
     ADD COLUMN otp_attempts SMALLINT NOT NULL DEFAULT 0 AFTER otp_expires_at,
     ADD COLUMN otp_sent_at DATETIME NULL AFTER otp_attempts',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0068 complete.' AS status;
