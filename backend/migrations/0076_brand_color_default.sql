-- Migration 0076: the app's accent/brand color used to be hardcoded jade
-- in the frontend's Tailwind config, completely independent of
-- CompanySettings.brand_color -- the color picker on Administration >
-- Company saved a value that nothing ever read. Now that the frontend
-- actually applies this column's value app-wide (see
-- src/utils/colorScale.ts's applyBrandColor), give it a real default
-- that matches the new brand: #3995BE, replacing the old placeholder
-- blue (#1D4ED8) that was itself never visually rendered anywhere.
--
-- Only updates the single company_settings row if it still holds the
-- untouched old default -- an admin who already saved a different color
-- (how, before this had any effect, is unlikely, but not impossible)
-- keeps their own choice rather than being silently overridden.
--
-- Idempotent -- re-running this after the row has already been updated
-- (or default in place) is a no-op, same convention as every other
-- migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0076_brand_color_default.sql

ALTER TABLE company_settings
    MODIFY COLUMN brand_color VARCHAR(20) NOT NULL DEFAULT '#3995BE';

UPDATE company_settings
SET brand_color = '#3995BE'
WHERE id = 1 AND brand_color = '#1D4ED8';
