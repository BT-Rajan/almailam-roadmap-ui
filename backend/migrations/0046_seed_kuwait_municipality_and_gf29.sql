-- Migration 0046: Seed a real Kuwait Municipality authority + the GF-29
-- design/licensing agreement form
--
-- Two things this closes:
--
-- 1. The three government_authorities rows this install shipped with
--    were placeholder Dubai-based demo data, not this firm's actual
--    jurisdiction -- wrong for a Kuwait-based practice (see
--    permit_catalog_items' own seed, migration 0040: "the firm only
--    ever files for these two Kuwait authorities"). They've since been
--    deleted from the admin UI; this adds the real one in their place
--    -- Kuwait Municipality -- rather than leaving Government Forms
--    with no usable authority at all.
--
-- 2. GF-29 (the Arabic design/licensing agreement contract, added to
--    STANDARD_GOVERNMENT_FORMS in migration 0045's PR) only existed as
--    a frontend "Load Standard Forms" seed -- nothing imports it
--    automatically, so it never actually showed up as a real,
--    fillable GovernmentForm row until an admin manually walks through
--    that dialog. This inserts the same form directly so it's usable
--    immediately after deploy, no manual import step required. The
--    STANDARD_GOVERNMENT_FORMS entry is left in place for reference/
--    re-import (e.g. onto a re-seeded authority) and still matches
--    this row's content exactly.
--
-- Idempotent -- guarded by NOT EXISTS checks against active (non-soft-
-- deleted) rows, same INSERT ... SELECT ... WHERE NOT EXISTS pattern
-- as migration 0040_permit_catalog_items.sql. Safe to re-run: if an
-- admin later renames or deletes this exact authority/form again,
-- re-running this migration recreates it rather than silently no-oping
-- forever, matching what "properly available after deploy" means here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0046_seed_kuwait_municipality_and_gf29.sql
--
-- SET NAMES utf8mb4 below is not optional: this file's title/description/
-- template columns are raw Arabic UTF-8 text (this file is saved as
-- UTF-8). Without declaring that, the mysql client's default
-- character-set-client (historically latin1) makes the server treat
-- every incoming multi-byte UTF-8 sequence as that many separate latin1
-- characters, silently mojibake-corrupting the Arabic text on insert
-- (confirmed while testing this migration -- the text still "looks
-- fine" to `mysql`'s own exit code, so nothing else would have caught
-- this).

SET NAMES utf8mb4;

INSERT INTO government_authorities (name, category, website, description)
SELECT * FROM (
    SELECT
        'Kuwait Municipality' AS name,
        'Municipality' AS category,
        'https://www.baladia.gov.kw' AS website,
        'Kuwait Municipality -- Engineering Licensing Department. Handles building permits, design approvals, and construction licensing for projects across Kuwait.' AS description
) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM government_authorities WHERE name = 'Kuwait Municipality' AND deleted_at IS NULL
);

INSERT INTO government_forms (
    authority_id, form_code, title, version, language, category, description,
    required_documents, preview_url, template, service_tags, status
)
SELECT * FROM (
    SELECT
        (SELECT id FROM government_authorities WHERE name = 'Kuwait Municipality' AND deleted_at IS NULL LIMIT 1) AS authority_id,
        'GF-29' AS form_code,
        'Design & Licensing Agreement Contract (Kuwait Municipality – Arabic)' AS title,
        'v1.0' AS version,
        'Arabic' AS language,
        'Agreement' AS category,
        'Arabic-language agreement contract between the engineering office and the property owner, submitted to Kuwait Municipality’s Engineering Licensing Department, covering design and licensing services and the plot’s Area/Sector/Block/Parcel details.' AS description,
        '[]' AS required_documents,
        NULL AS preview_url,
        'التاريخ: {{date}}

السادة / بلدية الكويت - إدارة التراخيص الهندسية المحترمين

تحية طيبة وبعد،،،

الموضوع: عقد الإتفاق

بالاشارة الى الموضوع اعلاه تم الاتفاق بين كلا من:

الطرف الأول: مكتب/ {{companyName}}
الطرف الثاني: السادة / {{clientName}}

على أن يقوم الطرف الأول بأعمال التصميم والترخيص للمشروع لدى الجهات المختصة، وذلك حسب المواصفات التي تم اختيارها من قبل المالك وحسب قوانين البلدية، وعليه يتم تمثيل المالك امام كافة الجهات المخولة لترخيص البناء المذكور، وتكون الأتعاب المالية خارج هذا العقد.

تفاصيل الموقع:
منطقة: {{plotArea}}
قطاع: {{plotSector}}
قطعة: {{plotBlock}}
قسيمة: {{plotParcel}}

وتفضلوا بقبول فائق الإحترام ،،

طرف أول (المكتب الهندسي): {{companyName}}          التوقيع: ………………
طرف ثاني (مالك العقار): {{clientName}}          التوقيع: ………………

الجهة التنظيمية: بلدية الكويت' AS template,
        '[]' AS service_tags,
        'Active' AS status
) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM government_forms WHERE form_code = 'GF-29' AND deleted_at IS NULL
);

SELECT 'Migration 0046 complete.' AS status;
