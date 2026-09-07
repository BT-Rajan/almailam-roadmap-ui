-- Migration 0069: admin-configurable subject/body for every automated
-- email the app sends (OTP codes, welcome/confirmation copies) --
-- the plain-text counterpart to migration 0064's admin-uploaded .docx
-- templates for Quotation/Contract documents (Administration > Documents
-- > Templates). This table backs the new Administration > Email Settings
-- > Templates tab (see email_template_service.py).
--
-- One row per fixed key (see app/models/email_template.py's
-- EMAIL_TEMPLATE_KEYS) -- not admin-creatable/deletable, since each key
-- corresponds to a real call site in the code. Seeded here with the
-- app's original hardcoded copy (see email_template_service.
-- DEFAULT_TEMPLATES, the single source of truth this mirrors) so
-- behavior is unchanged until an admin edits one. updated_by is set to
-- the lowest-id user on file (the bootstrap admin, in practice) since
-- this seed isn't performed by any particular logged-in admin.
--
-- Idempotent -- guarded by an information_schema check for the table,
-- and INSERT ... WHERE NOT EXISTS per row, same convention as every
-- other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0069_email_templates.sql

CREATE TABLE IF NOT EXISTS email_templates (
    id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    `key`       ENUM(
                  'client_onboarding_otp', 'client_welcome', 'project_created',
                  'requirement_otp', 'requirement_confirmed',
                  'quotation_otp', 'quotation_approved'
                ) NOT NULL UNIQUE,
    subject     VARCHAR(300) NOT NULL,
    body        TEXT NOT NULL,
    updated_by  BIGINT UNSIGNED NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_email_templates_updated_by FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'client_onboarding_otp', 'Your Al Mailam verification code',
  'Your verification code is {{ code }}.\n\nShare this code with the staff member handling your onboarding to confirm your email address. It expires in {{ validity_label }}.\n\nIf you didn''t request this, you can safely ignore this email.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'client_onboarding_otp');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'client_welcome', 'Welcome to Al Mailam -- your account is ready',
  'Dear {{ contact_person }},\n\nWelcome to Al Mailam! Your email has been verified and your onboarding is complete.\n\nHere are the details we have on file for you:\nClient type: {{ client_type }}\nName: {{ company_name }}\nContact person: {{ contact_person }}\nMobile: {{ mobile }}\nEmail: {{ email }}\nCity: {{ city }}\nPreferred language: {{ preferred_language }}\nPreferred contact channel: {{ preferred_channel }}\n\nYou can now sign in to the Client Portal to track your projects:\nCustomer ID: {{ customer_id }}\nTemporary password: {{ temporary_password }}\n\nFor your security, please sign in and change this password as soon as possible.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'client_welcome');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'project_created', 'New project created: {{ project_name }} ({{ project_no }})',
  'Dear {{ contact_person }},\n\nA new project has been created for {{ company_name }}:\n\nProject: {{ project_name }} ({{ project_no }})\nService: {{ service }}\n{{ site_address_line }}Start date: {{ start_date }}\nTarget date: {{ target_date }}\nAssigned engineer: {{ engineer_name }}\n\nWe''ll keep you updated as work progresses. You can also track this project''s status anytime through the Client Portal.\n\nThis is an informational message -- no action is needed.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'project_created');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'requirement_otp', 'Confirm the scope of work for {{ project_name }}',
  'Dear {{ contact_person }},\n\nYour verification code is {{ code }}.\n\nShare this code with the staff member handling project {{ project_name }} ({{ project_no }}) to confirm you accept the scope of work as written. It expires in {{ validity_label }}.\n\nIf you didn''t request this, you can safely ignore this email.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'requirement_otp');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'requirement_confirmed', 'Scope of work confirmed for {{ project_name }}',
  'Dear {{ contact_person }},\n\nThank you for confirming the scope of work for {{ project_name }} ({{ project_no }}):\n\n{{ scope_text }}\n\nThis is an informational message -- no action is needed.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'requirement_confirmed');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'quotation_otp', 'Your approval code for Quotation {{ quotation_no }}',
  'Dear {{ contact_person }},\n\nYour verification code is {{ code }}.\n\nShare this code with the staff member handling Quotation {{ quotation_no }} to confirm you accept it. It expires in {{ validity_label }}.\n\nIf you didn''t request this, you can safely ignore this email.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'quotation_otp');

INSERT INTO email_templates (`key`, subject, body, updated_by)
SELECT 'quotation_approved', 'Quotation {{ quotation_no }} confirmed',
  'Dear {{ contact_person }},\n\nThank you for confirming Quotation {{ quotation_no }}. Please find a copy attached.\n\nQuotation breakdown:\n{{ breakdown }}\n\n{{ scope_change_section }}{{ payment_plan_section }}This is an informational message -- no action is needed.',
  (SELECT id FROM users ORDER BY id ASC LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM email_templates WHERE `key` = 'quotation_approved');

SELECT 'Migration 0069 complete.' AS status;
