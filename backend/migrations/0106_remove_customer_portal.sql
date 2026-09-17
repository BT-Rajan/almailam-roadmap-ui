-- Migration 0106: remove the Customer Portal feature's schema footprint.
--
-- The Customer Portal (external client-facing login + project view,
-- unified onto the staff auth mechanism by migration 0026) has been
-- removed from the application entirely. This drops what that feature
-- left behind:
--   * users.customer_id / users.client_id (added by migration 0026) and
--     their FK/index/unique constraints
--   * 'Customer' from the users.role enum
--   * the 'client_welcome' email template (seeded by migration 0069),
--     which existed solely to deliver a new client's Customer Portal
--     login credentials
--
-- Idempotent -- every step is guarded by an information_schema check or
-- is naturally a no-op on a second run, same convention as every other
-- migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0106_remove_customer_portal.sql

-- Drop any Customer-role accounts first -- narrowing the role enum
-- below would otherwise fail with rows still using the value being
-- removed.
DELETE FROM users WHERE role = 'Customer';

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND CONSTRAINT_NAME = 'fk_users_client'
);
SET @sql = IF(@fk_exists > 0, 'ALTER TABLE users DROP FOREIGN KEY fk_users_client', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'idx_users_client'
);
SET @sql = IF(@idx_exists > 0, 'ALTER TABLE users DROP INDEX idx_users_client', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'client_id'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE users DROP COLUMN client_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'customer_id'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE users DROP COLUMN customer_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Same "MODIFY COLUMN with the full new value list" idempotent enum-
-- narrowing convention as migration 0080.
SET @enum_has_customer = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role'
    AND COLUMN_TYPE LIKE '%''Customer''%'
);
SET @sql = IF(@enum_has_customer > 0,
  'ALTER TABLE users
     MODIFY COLUMN role ENUM(''Administrator'',''Project Manager'',''Engineer'',''Document Controller'',''Viewer'')
       NOT NULL DEFAULT ''Viewer''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Also drop role_definitions/role_permissions rows for the removed
-- role, if role_service ever seeded them (see role_service._ensure_
-- seeded / _backfill_missing_roles). role_permissions cascades on
-- role_definitions delete, but deleted explicitly first for clarity.
DELETE FROM role_permissions WHERE role_id IN (
  SELECT id FROM role_definitions WHERE role = 'Customer'
);
DELETE FROM role_definitions WHERE role = 'Customer';

-- Drop the now-orphaned client_welcome template row, then narrow the
-- email_templates.key enum to drop that value too -- same "delete
-- data, then narrow the enum" order as migration 0080.
DELETE FROM email_templates WHERE `key` = 'client_welcome';

SET @enum_has_client_welcome = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'email_templates' AND COLUMN_NAME = 'key'
    AND COLUMN_TYPE LIKE '%client_welcome%'
);
SET @sql = IF(@enum_has_client_welcome > 0,
  'ALTER TABLE email_templates MODIFY COLUMN `key` ENUM(
     ''project_created'',
     ''requirement_confirmed'',
     ''quotation_approved'',
     ''contract_signed'',
     ''permit_application_submitted'', ''permit_response_received'',
     ''payment_received'', ''payment_reminder''
   ) NOT NULL UNIQUE',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0105 complete.' AS status;
