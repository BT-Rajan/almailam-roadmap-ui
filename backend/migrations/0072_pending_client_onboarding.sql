-- Migration 0072: staging table for the New Client wizard's
-- verify-before-create flow (see client_service.create_onboarding_request/
-- verify_onboarding_request_otp). A wizard submission is held here,
-- behind an email OTP (same otp_code_hash/otp_expires_at/otp_attempts/
-- otp_sent_at columns migrations 0066/0067/0068/0070 added elsewhere --
-- see EmailOtpMixin in app/models/mixins.py), until the client confirms
-- the code -- only then does a real `clients` row (and its contacts/
-- address/identification/document sub-records) get created. An
-- abandoned or never-verified submission just leaves an unconsumed row
-- here rather than a half-onboarded client.
--
-- Idempotent -- guarded by CREATE TABLE IF NOT EXISTS, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0072_pending_client_onboarding.sql

CREATE TABLE IF NOT EXISTS pending_client_onboardings (
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    payload         JSON NOT NULL,
    document        JSON NULL,
    otp_code_hash   VARCHAR(255) NULL,
    otp_expires_at  DATETIME NULL,
    otp_attempts    SMALLINT NOT NULL DEFAULT 0,
    otp_sent_at     DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0072 complete.' AS status;
