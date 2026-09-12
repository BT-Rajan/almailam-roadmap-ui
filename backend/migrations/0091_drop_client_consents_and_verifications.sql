-- Migration 0091: drop the client consent-tracking and verification-log
-- feature entirely.
--
-- client_consents (a formal, audited record of a client granting/
-- declining "Process Personal Information" / "Electronic Communication"
-- / "Process Documents") and client_verifications (a checklist-style log
-- of staff verifying a client's identity/documents, e.g. confirming a
-- Trade Licence) were both fully built on the backend -- models, schemas,
-- routes, service functions -- but never had a frontend caller of any
-- kind. Per product decision, the whole feature is removed rather than
-- built out.
--
-- Not touched by this migration: clients.email_consent/whatsapp_consent/
-- sms_consent (a separate, actively-used communication-preference
-- feature, set from ClientEditForm/ClientWizardForm's communication
-- preference fields -- nothing to do with this table) and
-- client_documents.verification_status (a plain per-document status
-- column, unrelated to the client_verifications audit table being
-- dropped here; it stays at whatever value it already has, typically
-- 'Pending', since create_verification was the only code that ever
-- advanced it and that was already unreachable from the frontend).
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0091_drop_client_consents_and_verifications.sql

SET @db := DATABASE();

SET @tbl_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'client_verifications'
);
SET @sql := IF(@tbl_exists > 0, 'DROP TABLE client_verifications', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @tbl_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'client_consents'
);
SET @sql := IF(@tbl_exists > 0, 'DROP TABLE client_consents', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0091 complete.' AS status;
