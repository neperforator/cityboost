-- Нагрузочный набор данных: 100 000 пользователей и 1 000 000 заявок.
-- Все сущности имеют детерминированные UUID (md5), поэтому скрипт идемпотентен.
-- Пользователи: bulkuser000001@example.test ... bulkuser100000@example.test
-- Пароль всех тестовых пользователей: password123
--
-- Запуск:
--   docker cp backend/scripts/seed_load_test.sql cityboost-db:/tmp/seed_load_test.sql
--   docker exec cityboost-db psql -U cityboost -d cityboost -v ON_ERROR_STOP=1 -f /tmp/seed_load_test.sql

\set ON_ERROR_STOP on
\timing on

BEGIN;

-- ── Пользователи ────────────────────────────────────────────────────────────
INSERT INTO users (
    id, name, email, password_hash, role,
    created_at, is_banned, is_verified
)
SELECT
    md5('cb_bulk_user_' || i)::uuid,
    'Тестовый пользователь ' || i,
    'bulkuser' || lpad(i::text, 6, '0') || '@example.com',
    '$2b$12$ZS.lstK2SBTtXPe88Nzowe0iEP9/3CtgPg0ms6gkKi2DTWnOxG2wS',
    'USER'::user_role,
    now() - (interval '400 days' + random() * interval '100 days'),
    false,
    true
FROM generate_series(1, 100000) AS s(i)
ON CONFLICT (id) DO NOTHING;

-- ── Тестовый администратор (для проверки админ-панели) ─────────────────────
INSERT INTO users (
    id, name, email, password_hash, role,
    created_at, is_banned, is_verified
)
VALUES (
    md5('cb_bulk_admin_1')::uuid,
    'Нагрузочный администратор',
    'loadadmin@example.com',
    '$2b$12$ZS.lstK2SBTtXPe88Nzowe0iEP9/3CtgPg0ms6gkKi2DTWnOxG2wS',
    'ADMIN'::user_role,
    now() - interval '200 days',
    false,
    true
)
ON CONFLICT (id) DO NOTHING;

-- ── Заявки ──────────────────────────────────────────────────────────────────
WITH admin_user AS (
    SELECT id
    FROM users
    WHERE role = 'ADMIN'
      AND email NOT LIKE 'bulkuser%@example.com'
      AND email <> 'loadadmin@example.com'
    ORDER BY created_at
    LIMIT 1
)
INSERT INTO tickets (
    id, user_id, assigned_to, title, description, status,
    latitude, longitude, address, close_reason, created_at, updated_at
)
SELECT
    md5('cb_bulk_ticket_' || i)::uuid,
    md5('cb_bulk_user_' || (1 + ((i - 1) % 100000)))::uuid,
    CASE WHEN r < 0.35 THEN NULL ELSE (SELECT id FROM admin_user) END,
    (ARRAY[
        'Яма на дороге',
        'Не горит фонарь',
        'Незаконная свалка',
        'Повреждена детская площадка',
        'Не убран снег',
        'Сломан светофор',
        'Протекает крыша',
        'Брошенный автомобиль',
        'Затоплен подвал',
        'Повреждён тротуар'
    ])[1 + floor(title_pick * 10)::int] || ' #' || i,
    'Автоматически сгенерированная заявка для нагрузочного тестирования. '
        || 'Номер: ' || i || '. Адрес: '
        || (ARRAY[
            'ул. Тверская', 'ул. Арбат', 'Ленинский проспект', 'ул. Гагарина',
            'Кутузовский проспект', 'ул. Пушкина', 'Садовая улица',
            'ул. Лесная', 'Мира проспект', 'ул. Центральная'
        ])[1 + floor(addr_pick * 10)::int]
        || ', д. ' || (1 + floor(house_pick * 120)::int) || '.',
    CASE
        WHEN r < 0.35 THEN 'NEW'::ticket_status
        WHEN r < 0.60 THEN 'IN_WORK'::ticket_status
        WHEN r < 0.85 THEN 'DONE'::ticket_status
        ELSE 'CLOSED'::ticket_status
    END,
    55.55 + lat_pick * 0.50,
    37.35 + lon_pick * 0.60,
    (ARRAY[
        'ул. Тверская', 'ул. Арбат', 'Ленинский проспект', 'ул. Гагарина',
        'Кутузовский проспект', 'ул. Пушкина', 'Садовая улица',
        'ул. Лесная', 'Мира проспект', 'ул. Центральная'
    ])[1 + floor(addr_pick * 10)::int]
        || ', д. ' || (1 + floor(house_pick * 120)::int),
    CASE WHEN r >= 0.85 THEN 'Проблема устранена' ELSE NULL END,
    now() - (age_pick * interval '365 days'),
    LEAST(
        now(),
        now() - (age_pick * interval '365 days') + (upd_pick * interval '10 days')
    )
FROM (
    SELECT
        i,
        random() AS r,
        random() AS title_pick,
        random() AS addr_pick,
        random() AS house_pick,
        random() AS lat_pick,
        random() AS lon_pick,
        random() AS age_pick,
        random() AS upd_pick
    FROM generate_series(1, 1000000) AS g(i)
) AS s
ON CONFLICT (id) DO NOTHING;

COMMIT;

ANALYZE users;
ANALYZE tickets;

\echo 'Готово. Итоговые размеры:'
SELECT
    (SELECT count(*) FROM users)   AS users,
    (SELECT count(*) FROM tickets) AS tickets;
