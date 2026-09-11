-- Migration 0090: widen projects.service from VARCHAR(100) to
-- VARCHAR(2000).
--
-- service is a comma-joined display summary of the distinct
-- Design/Supervision/Permit names picked in the New Project wizard
-- (see NewProjectWizardPage.handleServicesConfirmed), not a
-- normalized reference into the service catalog. Each catalog
-- service name alone can run to 150 characters (SelectedActivityIn.
-- serviceName), so joining more than a couple of distinct
-- services/categories -- an ordinary outcome with a large catalog --
-- overflowed 100 and made project creation fail with a bare "Please
-- check the 'service' field." for anyone who selected more than a
-- handful of services, no matter how the fields were actually filled
-- in. Widened to 2000 to match projects.description's own cap rather
-- than pick a new arbitrary ceiling.
--
-- Idempotent -- a MODIFY COLUMN is safe to rerun, same convention as
-- every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0090_widen_project_service_column.sql

ALTER TABLE projects
  MODIFY COLUMN service VARCHAR(2000) NOT NULL;

SELECT 'Migration 0090 complete.' AS status;
