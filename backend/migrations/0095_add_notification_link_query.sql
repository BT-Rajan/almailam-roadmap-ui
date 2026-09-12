-- Migration 0095: add notifications.link_query.
--
-- Every notification that links into a project (Quotation approved,
-- Contract signed, Payment recorded, ...) used the same
-- link_route_name="project-workspace" + link_params={"projectId": ...},
-- which always opens ProjectWorkspacePage.vue on its Requirement/
-- Overview default -- regardless of what the notification was actually
-- about. Clicking a "Quotation approved" notification landed on the
-- Scope card, not the quotation; clicking a payment notification landed
-- on the same generic Overview too. link_query lets a notification also
-- carry a router *query* (e.g. {"tab": "quotation"}) on top of
-- link_params' path params, which ProjectWorkspacePage.vue now reads
-- once on first load to pick its starting tab instead of always
-- defaulting to Overview (see the page's own comment on activeTab/
-- stageContext, and app/services/notification_service.py).
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here (e.g. migration 0054).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0095_add_notification_link_query.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'notifications' AND column_name = 'link_query'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE notifications ADD COLUMN link_query JSON NULL AFTER link_params',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0095 complete.' AS status;
