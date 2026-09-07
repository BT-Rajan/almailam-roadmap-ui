-- Migration 0066: replace client onboarding's manual "Under Review" step
-- with email OTP verification.
--
-- "Under Review" is renamed to "Pending Verification" -- staff no longer
-- eyeball a client's file and flip a status; instead they send the client
-- an email OTP and enter the code back once the client reads it out (see
-- client_service.send_onboarding_otp/verify_onboarding_otp). Confirming
-- the code is what now moves a client to "Ready", provisions their
-- Customer Portal login, and sends the welcome email (see
-- user_service.create_client_portal_user).
--
-- ENUM columns can't just be narrowed/renamed in place if existing rows
-- use the old value -- MySQL would either reject the ALTER outright
-- (strict mode) or silently blank those rows to '' (non-strict mode). Any
-- client currently sitting at "Under Review" is moved to "Pending
-- Verification", the direct replacement state, so no client jumps
-- backward or forward a step. Same convention as migration 0032. Each
-- step re-runs harmlessly if this migration is applied more than once.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0066_client_otp_verification.sql

UPDATE clients SET onboarding_state = 'Pending Verification' WHERE onboarding_state = 'Under Review';

ALTER TABLE clients
  MODIFY COLUMN onboarding_state ENUM('Information Required','Documents Required','Pending Verification','Ready','Rejected','Suspended')
    NOT NULL DEFAULT 'Ready';

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND COLUMN_NAME = 'otp_code_hash'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE clients
     ADD COLUMN otp_code_hash VARCHAR(255) NULL AFTER onboarding_notified_at,
     ADD COLUMN otp_expires_at DATETIME NULL AFTER otp_code_hash,
     ADD COLUMN otp_attempts SMALLINT NOT NULL DEFAULT 0 AFTER otp_expires_at,
     ADD COLUMN otp_sent_at DATETIME NULL AFTER otp_attempts',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0066 complete.' AS status;
