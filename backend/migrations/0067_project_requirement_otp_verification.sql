-- Migration 0067: client-facing email OTP confirmation for the
-- Requirement stage's scope of work.
--
-- Adds the same four otp_code_hash/otp_expires_at/otp_attempts/
-- otp_sent_at columns migration 0066 added to `clients` (see
-- EmailOtpMixin in app/models/mixins.py -- both tables now use the
-- same shared column set and the same shared app/core/otp.py logic,
-- rather than a second, differently-shaped OTP mechanism), plus
-- scope_client_confirmed_at: set once the client has confirmed the
-- scope of work by reading an OTP back to staff (see
-- project_service.send_requirement_otp/verify_requirement_otp),
-- distinct from scope_approved_at (staff's own internal sign-off).
-- Leaving the Requirement stage now requires both.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0067_project_requirement_otp_verification.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_client_confirmed_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects
     ADD COLUMN scope_client_confirmed_at DATETIME NULL AFTER scope_approved_by,
     ADD COLUMN otp_code_hash VARCHAR(255) NULL AFTER scope_client_confirmed_at,
     ADD COLUMN otp_expires_at DATETIME NULL AFTER otp_code_hash,
     ADD COLUMN otp_attempts SMALLINT NOT NULL DEFAULT 0 AFTER otp_expires_at,
     ADD COLUMN otp_sent_at DATETIME NULL AFTER otp_attempts',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0067 complete.' AS status;
