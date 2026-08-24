-- Migration 0034: per-project exclusion for execution activities.
--
-- is_optional (template + project) is documentation-only ("doesn't
-- gate anything" per migration 0022) and is shared across every
-- project since it's copied from the template. Staff need to drop an
-- activity out of the Completed-stage gate and out of the %complete
-- calculation for ONE specific project (e.g. no false ceiling on this
-- job) without touching the template that every other project's
-- snapshot was copied from -- hence a new column on
-- project_execution_steps only, not on execution_step_templates.
--
-- Run:
--   mysql -u <user> -p <database> < backend/migrations/0034_project_execution_step_exclusion.sql

ALTER TABLE project_execution_steps
    ADD COLUMN is_excluded TINYINT(1) NOT NULL DEFAULT 0 AFTER is_optional,
    ADD COLUMN excluded_reason VARCHAR(200) NULL AFTER is_excluded;

SELECT 'Migration 0034 complete.' AS status;
