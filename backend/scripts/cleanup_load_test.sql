-- Удаление нагрузочного набора, созданного seed_load_test.sql.
--
-- Запуск:
--   docker cp backend/scripts/cleanup_load_test.sql cityboost-db:/tmp/cleanup_load_test.sql
--   docker exec cityboost-db psql -U cityboost -d cityboost -v ON_ERROR_STOP=1 -f /tmp/cleanup_load_test.sql

\set ON_ERROR_STOP on
\timing on

BEGIN;

-- Сначала заявки: на них ссылаются ticket_files/history/comments.
DELETE FROM ticket_files
WHERE ticket_id IN (
    SELECT md5('cb_bulk_ticket_' || i)::uuid
    FROM generate_series(1, 1000000) AS s(i)
);

DELETE FROM ticket_history
WHERE ticket_id IN (
    SELECT md5('cb_bulk_ticket_' || i)::uuid
    FROM generate_series(1, 1000000) AS s(i)
);

DELETE FROM ticket_comments
WHERE ticket_id IN (
    SELECT md5('cb_bulk_ticket_' || i)::uuid
    FROM generate_series(1, 1000000) AS s(i)
);

DELETE FROM tickets
WHERE id IN (
    SELECT md5('cb_bulk_ticket_' || i)::uuid
    FROM generate_series(1, 1000000) AS s(i)
);

DELETE FROM users
WHERE id IN (
    SELECT md5('cb_bulk_user_' || i)::uuid
    FROM generate_series(1, 100000) AS s(i)
);

DELETE FROM users
WHERE id = md5('cb_bulk_admin_1')::uuid;

COMMIT;

VACUUM (ANALYZE) users;
VACUUM (ANALYZE) tickets;
