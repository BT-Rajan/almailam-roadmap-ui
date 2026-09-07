-- Migration 0075: admin-configurable email template for the project
-- handover confirmation OTP (Phase 6 of the parallel-tracks work) --
-- one new email_templates key, 'handover_otp', mirroring 'contract_otp'
-- from migration 0071. See email_template_service.DEFAULT_TEMPLATES
-- for the source of truth this seed mirrors.
--
-- Widens the `key` ENUM (MySQL requires re-listing all values on an
-- ALTER, not just the new one) then seeds the new row. Idempotent --
-- the ALTER is a no-op if the new value is already present, and the
-- INSERT guards with WHERE NOT EXISTS, same convention as every other
-- migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0075_handover_email_template.sql

SET @enum_has_handover_otp = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'email_templates' AND COLUMN_NAME = 'key'
    AND COLUMN_TYPE LIKE '%handover_otp%'
);
SET @sql = IF(@enum_has_handover_otp = 0,
  'ALTER TABLE email_templates MODIFY COLUMN `key` ENUM(
     ''client_onboarding_otp'', ''client_welcome'', ''project_created'',
     ''requirement_otp'', ''requirement_confirmed'',
     ''quotation_otp'', ''quotation_approved'',
     ''contract_otp'', ''contract_signed'',
     ''handover_otp''
   ) NOT NULL UNIQUE',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'handover_otp', 'Project {{ project_no }} is ready for hand-over',
  'Dear {{ contact_person }},\n\nProject {{ project_no }} is complete and fully paid. Please find the hand-over summary below.\n\n{{ checklist }}\n\nYour verification code is {{ code }}.\n\nShare this code with the staff member handling this project to confirm you accept the hand-over and close out the project. It expires in {{ validity_label }}.\n\nIf you didn''t request this, you can safely ignore this email.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'handover_otp');

SELECT 'Migration 0075 complete.' AS status;
