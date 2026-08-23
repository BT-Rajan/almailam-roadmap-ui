-- Migration 0029: repoint execution activity stage_key from the 5
-- approval-gate keys ('documents_signed', 'mew_approval', ...) to the
-- 7 project workflow stages ('Enquiry', 'Quotation', 'Contract',
-- 'Design', 'Government Submission') per the source PROJECT WORKFLOW
-- MAP diagram's Master Activity Registry. The field was always meant
-- to say which workflow stage an activity happens during, not which
-- approval gate it's loosely near -- see
-- app/services/execution_step_service.py's STAGE_KEYS comment.
--
-- Nothing currently reads this field for any enforcement decision (see
-- project_service._assert_stage_exit_criteria, which checks the 5
-- approval gates directly instead), so this is a pure relabeling with
-- no behavioral effect today -- it corrects what the data says so it's
-- available for a future per-stage-activity check without carrying the
-- wrong meaning forward.
--
-- Applied to both execution_step_templates (the admin-managed master
-- list) and project_execution_steps (every project's own snapshot
-- taken from it at creation time -- already-created projects have
-- their own copies that need the same correction). Matched by
-- sequence_number, not by the old stage_key value, since a single old
-- value ('documents_signed') maps to three different new stages
-- depending on which activity it was actually on.
--
-- Idempotent -- re-running assigns the same correct values again.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0029_execution_step_workflow_stage_keys.sql

UPDATE execution_step_templates
SET stage_key = CASE sequence_number
    WHEN 1 THEN 'Enquiry'
    WHEN 2 THEN 'Quotation'
    WHEN 3 THEN 'Contract'
    WHEN 4 THEN 'Contract'
    WHEN 5 THEN 'Contract'
    WHEN 6 THEN 'Government Submission'
    WHEN 7 THEN 'Contract'
    WHEN 8 THEN 'Design'
    WHEN 9 THEN 'Government Submission'
    WHEN 10 THEN 'Design'
    ELSE 'Government Submission'
END
WHERE sequence_number BETWEEN 1 AND 23;

UPDATE project_execution_steps
SET stage_key = CASE sequence_number
    WHEN 1 THEN 'Enquiry'
    WHEN 2 THEN 'Quotation'
    WHEN 3 THEN 'Contract'
    WHEN 4 THEN 'Contract'
    WHEN 5 THEN 'Contract'
    WHEN 6 THEN 'Government Submission'
    WHEN 7 THEN 'Contract'
    WHEN 8 THEN 'Design'
    WHEN 9 THEN 'Government Submission'
    WHEN 10 THEN 'Design'
    ELSE 'Government Submission'
END
WHERE sequence_number BETWEEN 1 AND 23;

SELECT 'Migration 0029 complete.' AS status;
