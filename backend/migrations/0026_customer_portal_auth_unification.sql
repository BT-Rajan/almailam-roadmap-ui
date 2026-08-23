-- Migration 0026: unify staff, Site Engineer Portal, and Customer Portal
-- logins onto one auth mechanism.
--
-- Adds users.customer_id (alternate login identifier, same idea as the
-- existing employee_id) and users.client_id (scopes a Customer account
-- to the one client record it's allowed to see), and adds 'Customer' to
-- the users.role enum. auth_service.login() now resolves username OR
-- employee_id OR customer_id, so all three frontends authenticate
-- through the same POST /api/auth/login.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0026_customer_portal_auth_unification.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'customer_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE users
     ADD COLUMN customer_id VARCHAR(30) NULL UNIQUE AFTER employee_id,
     ADD COLUMN client_id BIGINT UNSIGNED NULL AFTER customer_id,
     ADD CONSTRAINT fk_users_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
     ADD INDEX idx_users_client (client_id)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- MySQL/MariaDB have no "ADD VALUE IF NOT EXISTS" for enums -- MODIFY
-- COLUMN with the full new value list is the standard idempotent way to
-- extend one (re-running this with 'Customer' already present is a
-- harmless no-op).
ALTER TABLE users
  MODIFY COLUMN role ENUM('Administrator','Project Manager','Engineer','Document Controller','Viewer','Customer')
    NOT NULL DEFAULT 'Viewer';

SELECT 'Migration 0026 complete.' AS status;
