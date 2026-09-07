-- Migration 0071: admin-configurable email templates for the Contract
-- OTP flow (migration 0070) -- two new email_templates keys,
-- 'contract_otp' and 'contract_signed', mirroring 'quotation_otp'/
-- 'quotation_approved' from migration 0069. See email_template_service.
-- DEFAULT_TEMPLATES for the source of truth this seed mirrors.
--
-- Widens the `key` ENUM (MySQL requires re-listing all values on an
-- ALTER, not just the new ones) then seeds the 2 new rows. Idempotent --
-- the ALTER is a no-op if the new values are already present, and the
-- INSERTs each guard with WHERE NOT EXISTS, same convention as every
-- other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0071_contract_email_templates.sql

SET @enum_has_contract_otp = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'email_templates' AND COLUMN_NAME = 'key'
    AND COLUMN_TYPE LIKE '%contract_otp%'
);
SET @sql = IF(@enum_has_contract_otp = 0,
  'ALTER TABLE email_templates MODIFY COLUMN `key` ENUM(
     ''client_onboarding_otp'', ''client_welcome'', ''project_created'',
     ''requirement_otp'', ''requirement_confirmed'',
     ''quotation_otp'', ''quotation_approved'',
     ''contract_otp'', ''contract_signed''
   ) NOT NULL UNIQUE',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'contract_otp', 'Your signing code for Contract {{ contract_no }}',
  'Dear {{ contact_person }},\n\nYour verification code is {{ code }}.\n\nShare this code with the staff member handling Contract {{ contract_no }} to confirm you accept and sign it. It expires in {{ validity_label }}.\n\nIf you didn''t request this, you can safely ignore this email.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'contract_otp');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'contract_signed', 'Contract {{ contract_no }} signed',
  'Dear {{ contact_person }},\n\nThank you for confirming Contract {{ contract_no }}. Please find a copy attached.\n\nContract summary:\n{{ summary }}\n\nThis is an informational message -- no action is needed.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'contract_signed');

SELECT 'Migration 0071 complete.' AS status;
