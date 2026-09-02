-- Migration 0062: lets staff attach an optional proof-of-payment file
-- (receipt, transfer slip, etc.) to a recorded Payment -- see
-- payment_service.attach_payment_proof. Purely additive: financial
-- agreement update/delete (the other half of "payment plan CRUD") needs
-- no schema change, since Draft agreements already fully replace their
-- PaymentObligation rows on edit and cascade-delete them on removal.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (install.sh reapplies every migration
-- file on every run with no tracking of what already ran).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0062_payment_proof_and_plan_crud.sql

SET @db := DATABASE();

SET @proof_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'payments' AND column_name = 'proof_storage_key'
);
SET @sql := IF(@proof_col_exists = 0,
    "ALTER TABLE payments
        ADD COLUMN proof_storage_key VARCHAR(300) NULL AFTER created_at,
        ADD COLUMN proof_original_filename VARCHAR(255) NULL AFTER proof_storage_key,
        ADD COLUMN proof_file_size_bytes BIGINT UNSIGNED NULL AFTER proof_original_filename",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0062 complete.' AS status;
