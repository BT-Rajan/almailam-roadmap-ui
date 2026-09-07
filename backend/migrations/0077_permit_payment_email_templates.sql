-- Migration 0077: four new admin-configurable email templates --
-- 'permit_application_submitted' / 'permit_response_received' (FYI to
-- the client when a Government Submission is filed / gets a decision,
-- see submission_service.set_status) and 'payment_received' /
-- 'payment_reminder' (FYI when a payment is recorded, and the "due in
-- 2 days" reminder, see payment_service.record_payment/
-- check_and_notify_payment_reminders). Same "widen the enum, seed the
-- rows" shape as migration 0075's handover_otp. See
-- email_template_service.DEFAULT_TEMPLATES for the source of truth
-- this seed mirrors.
--
-- Idempotent -- the ALTER is a no-op if the new values are already
-- present, and each INSERT guards with WHERE NOT EXISTS, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0077_permit_payment_email_templates.sql

SET @enum_has_new_keys = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'email_templates' AND COLUMN_NAME = 'key'
    AND COLUMN_TYPE LIKE '%payment_reminder%'
);
SET @sql = IF(@enum_has_new_keys = 0,
  'ALTER TABLE email_templates MODIFY COLUMN `key` ENUM(
     ''client_onboarding_otp'', ''client_welcome'', ''project_created'',
     ''requirement_otp'', ''requirement_confirmed'',
     ''quotation_otp'', ''quotation_approved'',
     ''contract_otp'', ''contract_signed'',
     ''handover_otp'',
     ''permit_application_submitted'', ''permit_response_received'',
     ''payment_received'', ''payment_reminder''
   ) NOT NULL UNIQUE',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'permit_application_submitted', 'Your {{ form_title }} application has been submitted',
  'Dear {{ contact_person }},\n\nWe have submitted your {{ form_title }} application to {{ authority_name }} for project {{ project_name }} ({{ project_no }}).\n\nSubmission reference: {{ submission_no }}\nSubmitted on: {{ submitted_date }}\n\nThis is an informational message -- no action is needed. We''ll notify you as soon as we receive a response.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'permit_application_submitted');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'permit_response_received', 'Update on your {{ form_title }} application: {{ decision }}',
  'Dear {{ contact_person }},\n\n{{ authority_name }} has responded to your {{ form_title }} application for project {{ project_name }} ({{ project_no }}).\n\nSubmission reference: {{ submission_no }}\nDecision: {{ decision }}\nDecision date: {{ decision_date }}\n\nThis is an informational message -- no action is needed.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'permit_response_received');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'payment_received', 'Payment received for {{ project_name }} ({{ project_no }})',
  'Dear {{ contact_person }},\n\nWe confirm receipt of your payment for project {{ project_name }} ({{ project_no }}).\n\nAmount received: {{ amount }} {{ currency }}\nPayment date: {{ payment_date }}\nReference: {{ reference_number }}\n\nThis is an informational message -- no action is needed. Thank you.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'payment_received');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'payment_reminder', 'Payment reminder: {{ amount }} {{ currency }} due {{ due_date }} for {{ project_name }}',
  'Dear {{ contact_person }},\n\nThis is a reminder that a payment for project {{ project_name }} ({{ project_no }}) is due in 2 days, on {{ due_date }}.\n\nDescription: {{ description }}\nAmount due: {{ amount }} {{ currency }}\n\nThis is an informational message -- no action is needed if payment is already arranged.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'payment_reminder');

SELECT 'Migration 0077 complete.' AS status;
