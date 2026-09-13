-- Migration 0096: add users.salutation.
--
-- Generated documents (Quotation/Contract "Prepared By") previously
-- printed a staff member's bare full_name with no title -- this column
-- lets an admin record the correct "Mr."/"Ms." for a user (see
-- Administration > Users) so document_template_service._user_name can
-- prefix it. Nullable and never defaulted: unlike a client's company
-- name (see the M/s. prefix added in document_template_service.py,
-- which needs no per-record data), guessing a person's salutation from
-- nothing would risk getting it wrong, so a user with no salutation set
-- simply keeps printing as their bare name, same as before this
-- migration.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here (e.g. migration 0095).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0096_user_salutation.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'users' AND column_name = 'salutation'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE users ADD COLUMN salutation ENUM('Mr.', 'Ms.') NULL AFTER full_name",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0096 complete.' AS status;
