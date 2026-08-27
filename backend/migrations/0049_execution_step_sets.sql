-- Migration 0049: admin-configurable execution step sets, per project
--
-- Replaces the single implicit global execution-step template (every
-- project got the exact same 23 steps regardless of what work it
-- actually involved) with named, admin-managed step sets --
-- execution_step_set_templates -- that a project is assigned at
-- creation (projects.step_set_id). "What steps for which project" is
-- now a real configuration instead of a hardcoded assumption.
--
-- Also retires the old _AUTO_FILL_TRIGGERS Python dict (hardcoded
-- sequence_number -> trigger mapping, which could only ever describe
-- one fixed step order) in favour of a trigger_key column carried
-- directly on each step -- necessary now that more than one step set
-- can exist, each with its own numbering.
--
-- This install's existing 23 steps, and every existing project's
-- already-snapshotted checklist, are backfilled onto one seeded
-- "Standard Process" step set so nothing about an already-running
-- project changes underneath it.
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0049_execution_step_sets.sql

SET @db := DATABASE();

-- ---------------------------------------------------------------------------
-- Part 1: execution_step_set_templates table + seeded "Standard Process" row
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS execution_step_set_templates (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    description     VARCHAR(500) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO execution_step_set_templates (name, description)
SELECT * FROM (
    SELECT 'Standard Process' AS name, 'The original 23-step process (First Meeting through Lighting drawings), unchanged.' AS description
) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM execution_step_set_templates WHERE name = 'Standard Process' AND deleted_at IS NULL
);

SET @standard_set_id := (SELECT id FROM execution_step_set_templates WHERE name = 'Standard Process' AND deleted_at IS NULL LIMIT 1);

-- ---------------------------------------------------------------------------
-- Part 2: execution_step_templates -> step_set_id + trigger_key
-- ---------------------------------------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'execution_step_templates' AND column_name = 'step_set_id'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE execution_step_templates ADD COLUMN step_set_id BIGINT UNSIGNED NULL AFTER id',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE execution_step_templates SET step_set_id = @standard_set_id WHERE step_set_id IS NULL;

SET @needs_not_null := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'execution_step_templates' AND column_name = 'step_set_id' AND is_nullable = 'YES'
);
SET @sql := IF(@needs_not_null > 0,
    'ALTER TABLE execution_step_templates MODIFY COLUMN step_set_id BIGINT UNSIGNED NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'execution_step_templates' AND CONSTRAINT_NAME = 'fk_execution_step_templates_step_set'
);
SET @sql := IF(@constraint_exists = 0,
    'ALTER TABLE execution_step_templates ADD CONSTRAINT fk_execution_step_templates_step_set FOREIGN KEY (step_set_id) REFERENCES execution_step_set_templates(id) ON DELETE CASCADE',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'execution_step_templates' AND INDEX_NAME = 'idx_execution_step_templates_step_set'
);
SET @sql := IF(@index_exists = 0,
    'CREATE INDEX idx_execution_step_templates_step_set ON execution_step_templates (step_set_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'execution_step_templates' AND column_name = 'trigger_key'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE execution_step_templates ADD COLUMN trigger_key VARCHAR(60) NULL AFTER is_optional',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill trigger_key from the old hardcoded _AUTO_FILL_TRIGGERS dict
-- (sequence_number -> trigger), scoped to the Standard Process set --
-- the only set that existed when these sequence numbers meant anything.
UPDATE execution_step_templates SET trigger_key = 'quotation_created'      WHERE step_set_id = @standard_set_id AND sequence_number = 2 AND trigger_key IS NULL;
UPDATE execution_step_templates SET trigger_key = 'gate:documents_signed'  WHERE step_set_id = @standard_set_id AND sequence_number = 5 AND trigger_key IS NULL;
UPDATE execution_step_templates SET trigger_key = 'gate:mew_approval'      WHERE step_set_id = @standard_set_id AND sequence_number = 6 AND trigger_key IS NULL;
UPDATE execution_step_templates SET trigger_key = 'contract_created'       WHERE step_set_id = @standard_set_id AND sequence_number = 7 AND trigger_key IS NULL;
UPDATE execution_step_templates SET trigger_key = 'gate:architectural_approval' WHERE step_set_id = @standard_set_id AND sequence_number = 8 AND trigger_key IS NULL;
UPDATE execution_step_templates SET trigger_key = 'gate:submit_baladia_kfd'     WHERE step_set_id = @standard_set_id AND sequence_number = 9 AND trigger_key IS NULL;

-- ---------------------------------------------------------------------------
-- Part 3: projects -> step_set_id
-- ---------------------------------------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'step_set_id'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE projects ADD COLUMN step_set_id BIGINT UNSIGNED NULL AFTER deviation_notes',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE projects SET step_set_id = @standard_set_id WHERE step_set_id IS NULL;

SET @constraint_exists := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'projects' AND CONSTRAINT_NAME = 'fk_projects_step_set'
);
SET @sql := IF(@constraint_exists = 0,
    'ALTER TABLE projects ADD CONSTRAINT fk_projects_step_set FOREIGN KEY (step_set_id) REFERENCES execution_step_set_templates(id) ON DELETE RESTRICT',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 4: project_execution_steps -> trigger_key + is_custom
-- ---------------------------------------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_execution_steps' AND column_name = 'trigger_key'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE project_execution_steps ADD COLUMN trigger_key VARCHAR(60) NULL AFTER is_optional',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_execution_steps' AND column_name = 'is_custom'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE project_execution_steps ADD COLUMN is_custom TINYINT(1) NOT NULL DEFAULT 0 AFTER trigger_key',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Every existing project_execution_steps row was snapshotted 1:1 from
-- the (only, at the time) global template, so its sequence_number
-- still matches that template's own numbering -- same backfill mapping
-- as Part 2 above, applied here per-project rather than per-template.
UPDATE project_execution_steps SET trigger_key = 'quotation_created'      WHERE sequence_number = 2 AND trigger_key IS NULL AND is_custom = 0;
UPDATE project_execution_steps SET trigger_key = 'gate:documents_signed'  WHERE sequence_number = 5 AND trigger_key IS NULL AND is_custom = 0;
UPDATE project_execution_steps SET trigger_key = 'gate:mew_approval'      WHERE sequence_number = 6 AND trigger_key IS NULL AND is_custom = 0;
UPDATE project_execution_steps SET trigger_key = 'contract_created'       WHERE sequence_number = 7 AND trigger_key IS NULL AND is_custom = 0;
UPDATE project_execution_steps SET trigger_key = 'gate:architectural_approval' WHERE sequence_number = 8 AND trigger_key IS NULL AND is_custom = 0;
UPDATE project_execution_steps SET trigger_key = 'gate:submit_baladia_kfd'     WHERE sequence_number = 9 AND trigger_key IS NULL AND is_custom = 0;

SELECT 'Migration 0049 complete.' AS status;
