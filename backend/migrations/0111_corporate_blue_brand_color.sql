-- Migration 0111: Corporate blue as the default brand color
--
-- The default brand color was a muted teal-blue (#3995BE). The customer's
-- corporate color is a stronger blue, so the default becomes #1D4ED8.
-- Only rows still on the old, untouched default are moved; a color an
-- admin picked in Administration > Company is left alone. Idempotent.

ALTER TABLE company_settings
    MODIFY brand_color VARCHAR(20) NOT NULL DEFAULT '#1D4ED8';

UPDATE company_settings
    SET brand_color = '#1D4ED8'
    WHERE UPPER(brand_color) = '#3995BE';
