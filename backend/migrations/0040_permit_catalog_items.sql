-- permit_catalog_items was referenced by app/models/permit_catalog.py and
-- queried by /api/permit-catalog/permits, but the table itself was never
-- added to schema.sql -- a fresh install 500s the New Project wizard's
-- Permits step the moment it loads. This creates it (matching the model's
-- columns exactly) and seeds Almailam's actual two permit types, since the
-- firm only ever files for these two Kuwait authorities.

CREATE TABLE IF NOT EXISTS permit_catalog_items (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO permit_catalog_items (name)
SELECT * FROM (SELECT 'Baladia Permits' AS name) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM permit_catalog_items WHERE name = 'Baladia Permits' AND deleted_at IS NULL
);

INSERT INTO permit_catalog_items (name)
SELECT * FROM (SELECT 'KFD Permits' AS name) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM permit_catalog_items WHERE name = 'KFD Permits' AND deleted_at IS NULL
);
