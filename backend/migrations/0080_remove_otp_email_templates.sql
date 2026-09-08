-- Migration 0080: remove the five email templates that backed the old
-- OTP-code confirmation flows -- 'client_onboarding_otp', 'requirement_otp',
-- 'quotation_otp', 'contract_otp', 'handover_otp'. Every one of those
-- confirmation steps (client onboarding, Requirement scope, Quotation
-- approval, Contract signing, project hand-over) now confirms via a
-- signed-document upload instead of an emailed code (see
-- quotation_service.confirm_quotation_approval and its siblings in
-- contract_service/project_service/client_service), so none of these
-- five keys has a remaining call site -- see
-- email_template_service.DEFAULT_TEMPLATES/MERGE_FIELD_CATALOG and
-- app/models/email_template.py's EMAIL_TEMPLATE_KEYS, both already
-- trimmed to match.
--
-- Deletes the five now-orphaned rows first, then narrows the `key`
-- enum to drop those values -- same "delete data, then narrow the
-- enum" order as any other enum-shrink here. Also repoints
-- 'client_welcome''s stock wording, which used to claim "your email
-- has been verified" (true when it followed an OTP confirmation, not
-- true now that onboarding is confirmed via a signed-document upload)
-- -- see email_template_service.DEFAULT_TEMPLATES for the corrected
-- copy this mirrors. Guarded to only touch a row that still has the
-- exact original wording, so an admin's own edit to this template is
-- left alone.
--
-- Idempotent -- the DELETEs are no-ops once the rows are gone, the
-- ALTER is guarded to only run while the enum still lists a removed
-- key, and the UPDATE is a no-op once the old wording is gone.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0080_remove_otp_email_templates.sql

DELETE FROM email_templates WHERE `key` IN (
  'client_onboarding_otp', 'requirement_otp', 'quotation_otp', 'contract_otp', 'handover_otp'
);

UPDATE email_templates
SET body = REPLACE(
  body,
  'Welcome to Al Mailam! Your email has been verified and your onboarding is complete.',
  'Welcome to Al Mailam! Your onboarding is complete.'
)
WHERE `key` = 'client_welcome'
  AND body LIKE '%Your email has been verified and your onboarding is complete.%';

SET @enum_has_otp_keys = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'email_templates' AND COLUMN_NAME = 'key'
    AND COLUMN_TYPE LIKE '%client_onboarding_otp%'
);
SET @sql = IF(@enum_has_otp_keys > 0,
  'ALTER TABLE email_templates MODIFY COLUMN `key` ENUM(
     ''client_welcome'', ''project_created'',
     ''requirement_confirmed'',
     ''quotation_approved'',
     ''contract_signed'',
     ''permit_application_submitted'', ''permit_response_received'',
     ''payment_received'', ''payment_reminder''
   ) NOT NULL UNIQUE',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0080 complete.' AS status;
