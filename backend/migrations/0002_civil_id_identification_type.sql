-- Migration 0002: identification type localized to Kuwait (Civil ID)
--
-- IDENTIFICATION_TYPES changed from ("Emirates ID", "Passport", "Trade
-- Licence", "Other") to ("Civil ID", "Passport", "Trade Licence",
-- "Other") -- this app is for a Kuwait-based company; "Emirates ID" (a
-- UAE national ID) was never the correct identification type to offer.
--
-- ENUM columns can't just be narrowed directly if existing rows use a
-- value being removed -- MySQL would either reject the ALTER outright
-- (strict mode) or silently blank those rows to '' (non-strict mode).
-- Safe order: widen the enum to allow both values, migrate the data,
-- then narrow it. Each step re-runs harmlessly if this migration is
-- applied more than once.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0002_civil_id_identification_type.sql

ALTER TABLE client_identifications
  MODIFY COLUMN document_type ENUM('Emirates ID','Civil ID','Passport','Trade Licence','Other') NOT NULL;

UPDATE client_identifications SET document_type = 'Civil ID' WHERE document_type = 'Emirates ID';

ALTER TABLE client_identifications
  MODIFY COLUMN document_type ENUM('Civil ID','Passport','Trade Licence','Other') NOT NULL;

SELECT 'Migration 0002 complete.' AS status;
