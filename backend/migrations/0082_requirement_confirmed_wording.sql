-- Migration 0082: fix the requirement_confirmed email template's
-- wording -- it used to thank the client for "confirming" the scope of
-- work themselves, back when leaving the Requirement stage required
-- the client's own signed-document upload. That client-facing step is
-- gone (see project_service.confirm_requirement_scope): the project
-- associate now confirms the scope directly, no client artifact
-- involved, so the email is now a plain FYI that the scope has been
-- finalized rather than a thank-you for a confirmation the client
-- never made.
--
-- Guarded to only touch a row that still has the exact original
-- subject/wording, so an admin's own edit to this template is left
-- alone -- same idempotent, non-destructive shape as migration 0080's
-- client_welcome fix.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0082_requirement_confirmed_wording.sql

UPDATE email_templates
SET subject = 'Scope of work finalized for {{ project_name }}'
WHERE `key` = 'requirement_confirmed'
  AND subject = 'Scope of work confirmed for {{ project_name }}';

UPDATE email_templates
SET body = REPLACE(
  body,
  'Thank you for confirming the scope of work for {{ project_name }} ({{ project_no }}):',
  'The scope of work for {{ project_name }} ({{ project_no }}) has been finalized:'
)
WHERE `key` = 'requirement_confirmed'
  AND body LIKE '%Thank you for confirming the scope of work for {{ project_name }} ({{ project_no }}):%';

SELECT 'Migration 0082 complete.' AS status;
