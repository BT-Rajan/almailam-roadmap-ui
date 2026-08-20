-- Migration 0014: configurable role permissions
--
-- Replaces the hardcoded ROLE_PERMISSIONS dict in core/permissions.py
-- with an admin-configurable matrix, same reasoning and pattern as
-- migration 0009's service catalog: the role *names* stay fixed (the
-- users.role DB enum and request validation still use core.permissions
-- .ROLES), but what each role can do per module is now stored data.
--
-- Tables are created empty here -- seeding from the previous hardcoded
-- ROLE_DESCRIPTIONS/ROLE_PERMISSIONS values happens in Python
-- (role_service._ensure_seeded) the first time the roles endpoint is
-- read, same lazy-seed approach as service_catalog_service, so this
-- migration doesn't need to duplicate that data as raw SQL.
--
-- Idempotent -- CREATE TABLE IF NOT EXISTS is naturally safe to re-run,
-- same pattern as earlier migrations.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0014_role_permissions.sql

CREATE TABLE IF NOT EXISTS role_definitions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role            VARCHAR(50) NOT NULL,
    description     VARCHAR(500) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_role_definitions_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS role_permissions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role_id         BIGINT UNSIGNED NOT NULL,
    module          VARCHAR(50) NOT NULL,
    can_view        TINYINT(1) NOT NULL DEFAULT 0,
    can_edit        TINYINT(1) NOT NULL DEFAULT 0,
    can_delete      TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY (role_id) REFERENCES role_definitions(id) ON DELETE CASCADE,
    UNIQUE KEY uq_role_permissions_role_module (role_id, module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0014 complete.' AS status;
