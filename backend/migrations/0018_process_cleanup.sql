-- Migration 0018: consolidate the project process down to exactly the
-- two things it should be -- the 5-stage Project Approval Process
-- (migration 0017) and the 23-step execution checklist (migration
-- 0016) -- and cut the rest.
--
-- Two things happen here:
--
-- 1. DROPS workflow_templates / workflow_stages (the generic,
--    admin-editable "Workflow Configuration" system). It was never
--    wired to anything real: projects.current_stage is a fixed DB
--    ENUM, not driven by these rows, so editing a template here had
--    zero effect on any actual project. It only duplicated (and,
--    since its own DEFAULT_STAGES seed dropped "Correction", drifted
--    from) the real 9-stage stage list. Deliberately NOT touching
--    projects.current_stage or its ENUM/transition rules here -- that
--    pipeline is a distinct, legitimate concept (the sales/lifecycle
--    stage) and stays exactly as it is.
--
-- 2. Adds stage_key (grouping every execution step under one of the 5
--    approval stages, so the project UI can show one unified process
--    view instead of a separate tab and a separate modal that never
--    talked to each other) and is_optional + a Waived status (with
--    audit fields, mirroring the existing Cancelled/Waived pattern
--    used for payment obligations) so a step can be marked as not
--    applicable for a given client rather than blocking the checklist
--    forever.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- migrations 0004/0008-0010/0013/0015. install.sh has no migration-
-- tracking table; it reapplies every file in this directory on every
-- run, so each one has to tolerate being run again against a database
-- it's already been applied to.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0018_process_cleanup.sql

-- ---------------------------------------------------------------------------
-- Part 1: drop the dead, disconnected workflow-template system
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS workflow_stages;
DROP TABLE IF EXISTS workflow_templates;

-- ---------------------------------------------------------------------------
-- Part 2: stage grouping + optional/waivable steps
-- ---------------------------------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'execution_step_templates' AND COLUMN_NAME = 'stage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE execution_step_templates ADD COLUMN stage_key VARCHAR(40) NOT NULL DEFAULT '''' AFTER weight_percentage',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'execution_step_templates' AND COLUMN_NAME = 'is_optional'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE execution_step_templates ADD COLUMN is_optional TINYINT(1) NOT NULL DEFAULT 0 AFTER stage_key',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'stage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN stage_key VARCHAR(40) NOT NULL DEFAULT '''' AFTER weight_percentage',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'is_optional'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN is_optional TINYINT(1) NOT NULL DEFAULT 0 AFTER stage_key',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'waived_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN waived_at DATETIME NULL AFTER completed_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'waived_by'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN waived_by BIGINT UNSIGNED NULL AFTER waived_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'waived_reason'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN waived_reason VARCHAR(500) NULL AFTER waived_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps'
    AND CONSTRAINT_NAME = 'fk_project_execution_steps_waived_by'
);
SET @sql = IF(@constraint_exists = 0,
  'ALTER TABLE project_execution_steps ADD CONSTRAINT fk_project_execution_steps_waived_by FOREIGN KEY (waived_by) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- MODIFY COLUMN is naturally idempotent -- re-running the same ENUM
-- definition against a column that already has it is a safe no-op, so
-- this doesn't need an information_schema guard (same as migration
-- 0013's ENUM widening).
ALTER TABLE project_execution_steps
  MODIFY COLUMN status ENUM('Pending','Completed','Waived') NOT NULL DEFAULT 'Pending';

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'approval_process_templates' AND COLUMN_NAME = 'stage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE approval_process_templates ADD COLUMN stage_key VARCHAR(40) NOT NULL DEFAULT '''' AFTER name',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'approval_process_templates' AND COLUMN_NAME = 'is_optional'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE approval_process_templates ADD COLUMN is_optional TINYINT(1) NOT NULL DEFAULT 0 AFTER stage_key',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'stage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN stage_key VARCHAR(40) NOT NULL DEFAULT '''' AFTER name',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'is_optional'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN is_optional TINYINT(1) NOT NULL DEFAULT 0 AFTER stage_key',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'waived_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN waived_at DATETIME NULL AFTER completed_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'waived_by'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN waived_by BIGINT UNSIGNED NULL AFTER waived_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'waived_reason'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN waived_reason VARCHAR(500) NULL AFTER waived_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps'
    AND CONSTRAINT_NAME = 'fk_project_approval_steps_waived_by'
);
SET @sql = IF(@constraint_exists = 0,
  'ALTER TABLE project_approval_steps ADD CONSTRAINT fk_project_approval_steps_waived_by FOREIGN KEY (waived_by) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

ALTER TABLE project_approval_steps
  MODIFY COLUMN status ENUM('Pending','Completed','Waived') NOT NULL DEFAULT 'Pending';

-- ---------------------------------------------------------------------------
-- Part 3: backfill stage_key on the 5 approval stages -- each stage is
-- its own group, so this is a direct 1:1 name -> key mapping.
-- ---------------------------------------------------------------------------

UPDATE approval_process_templates SET stage_key = 'documents_signed' WHERE name = 'Documents Signed';
UPDATE approval_process_templates SET stage_key = 'mew_approval' WHERE name = 'MEW Approval';
UPDATE approval_process_templates SET stage_key = 'architectural_approval' WHERE name = 'Architectural Design Approved by Client';
UPDATE approval_process_templates SET stage_key = 'submit_baladia_kfd' WHERE name = 'Submit to Baladia or KFD';
UPDATE approval_process_templates SET stage_key = 'permit_approved' WHERE name = 'Permit Approved';

UPDATE project_approval_steps SET stage_key = 'documents_signed' WHERE name = 'Documents Signed';
UPDATE project_approval_steps SET stage_key = 'mew_approval' WHERE name = 'MEW Approval';
UPDATE project_approval_steps SET stage_key = 'architectural_approval' WHERE name = 'Architectural Design Approved by Client';
UPDATE project_approval_steps SET stage_key = 'submit_baladia_kfd' WHERE name = 'Submit to Baladia or KFD';
UPDATE project_approval_steps SET stage_key = 'permit_approved' WHERE name = 'Permit Approved';

-- ---------------------------------------------------------------------------
-- Part 4: backfill stage_key on the 23 execution steps, grouping each
-- tangible-act step under the approval stage its outcome belongs to:
--   documents_signed        -- steps 1-5, 7 (everything that leads up
--                               to and includes signing/contracting)
--   mew_approval             -- step 6 (the MEW request itself)
--   architectural_approval   -- steps 8, 10 (the architectural + 3D
--                               design the client signs off on)
--   submit_baladia_kfd       -- step 9 and steps 11-23 (the initial
--                               drawing submission plus the full
--                               structural/interior/MEP technical
--                               package that follows it into the same
--                               Baladia/KFD submission)
-- "Permit Approved" (stage 5) is a pure external gate with no
-- execution steps of its own -- nothing in this checklist maps there.
-- Matched by sequence_number, which is stable and unique per template
-- / per project (see the unique constraint on project_execution_steps).
-- ---------------------------------------------------------------------------

UPDATE execution_step_templates SET stage_key = 'documents_signed' WHERE sequence_number IN (1, 2, 3, 4, 5, 7);
UPDATE execution_step_templates SET stage_key = 'mew_approval' WHERE sequence_number = 6;
UPDATE execution_step_templates SET stage_key = 'architectural_approval' WHERE sequence_number IN (8, 10);
UPDATE execution_step_templates SET stage_key = 'submit_baladia_kfd' WHERE sequence_number IN (9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23);

UPDATE project_execution_steps SET stage_key = 'documents_signed' WHERE sequence_number IN (1, 2, 3, 4, 5, 7);
UPDATE project_execution_steps SET stage_key = 'mew_approval' WHERE sequence_number = 6;
UPDATE project_execution_steps SET stage_key = 'architectural_approval' WHERE sequence_number IN (8, 10);
UPDATE project_execution_steps SET stage_key = 'submit_baladia_kfd' WHERE sequence_number IN (9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23);

-- ---------------------------------------------------------------------------
-- Part 5: flag the steps that are commonly client-dependent as
-- waivable (is_optional) -- 3D design, the interior/furniture/
-- bathroom finishing drawings, and the A/C, ceiling and lighting
-- drawings are the ones real clients most often don't want, per the
-- source process document. The core architectural/structural/MEP
-- submission steps stay mandatory. Admin can adjust this per step from
-- the Execution Steps admin page after this migration runs.
-- ---------------------------------------------------------------------------

UPDATE execution_step_templates SET is_optional = 1 WHERE sequence_number IN (10, 14, 15, 16, 17, 20, 21, 22, 23);
UPDATE project_execution_steps SET is_optional = 1 WHERE sequence_number IN (10, 14, 15, 16, 17, 20, 21, 22, 23);

SELECT 'Migration 0018 complete.' AS status;
