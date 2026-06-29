"""
Полное интеграционное тестирование всех функций CityBoost.

Запуск: docker compose run --rm backend python -m tests.full_test
"""

from __future__ import annotations

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import io
import uuid

import httpx

BASE_URL = "http://backend:8000/api/v1"

passed = 0
failed = 0


def ok(msg: str):
    global passed
    passed += 1
    print(f"  ✅ {msg}")


def fail(msg: str, detail: str = ""):
    global failed
    failed += 1
    text = f"  ❌ {msg}"
    if detail:
        text += f"\n     {detail}"
    print(text)


async def test_auth_flow(client: httpx.AsyncClient):
    print("\n═══════════════════════════════════════════")
    print("1. АУТЕНТИФИКАЦИЯ")
    print("═══════════════════════════════════════════")

    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    password = "StrongPass1"

    # 1.1 Регистрация
    r = await client.post(f"{BASE_URL}/auth/register", json={
        "name": "Тестовый Пользователь", "email": email, "password": password,
    })
    assert r.status_code == 201, f"Register failed: {r.text}"
    ok("Регистрация нового пользователя — 201")

    # 1.2 Дубликат email
    r = await client.post(f"{BASE_URL}/auth/register", json={
        "name": "Дубликат", "email": email, "password": password,
    })
    assert r.status_code == 409
    ok("Регистрация с дубликатом email — 409 Conflict")

    # 1.3 Слабый пароль (pydantic schema validation: min_length=8 → 422)
    r = await client.post(f"{BASE_URL}/auth/register", json={
        "name": "Weak", "email": "weak@test.com", "password": "123",
    })
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    ok("Регистрация со слабым паролем — 422 (pydantic validation)")

    # 1.4 Логин
    r = await client.post(f"{BASE_URL}/auth/login", json={
        "email": email, "password": password,
    })
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token
    ok("Логин — 200, получен токен")

    headers = {"Authorization": f"Bearer {token}"}

    # 1.5 Неверный пароль
    r = await client.post(f"{BASE_URL}/auth/login", json={
        "email": email, "password": "WrongPass1",
    })
    assert r.status_code == 401
    ok("Логин с неверным паролем — 401")

    # 1.6 Несуществующий email
    r = await client.post(f"{BASE_URL}/auth/login", json={
        "email": "nonexistent@test.com", "password": password,
    })
    assert r.status_code == 401
    ok("Логин с несуществующим email — 401")

    # 1.7 Профиль
    r = await client.get(f"{BASE_URL}/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == email
    assert me["name"] == "Тестовый Пользователь"
    ok("GET /auth/me — профиль получен")

    # 1.8 Профиль без токена
    r = await client.get(f"{BASE_URL}/auth/me")
    assert r.status_code == 401
    ok("GET /auth/me без токена — 401")

    # 1.9 Обновление профиля
    r = await client.patch(f"{BASE_URL}/auth/me",
        json={"name": "Новое Имя"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Новое Имя"
    ok("PATCH /auth/me — имя обновлено")

    # 1.10 Загрузка аватара
    avatar_bytes = io.BytesIO()
    avatar_bytes.write(b"fake-avatar-data")
    avatar_bytes.seek(0)
    # Hmm, we need a valid PNG for avatar. Let's use our mini PNG.
    # Actually we'll test this separately below.

    return email, password, token, headers


async def test_forgot_reset(client: httpx.AsyncClient, email: str):
    print("\n═══════════════════════════════════════════")
    print("2. СБРОС ПАРОЛЯ")
    print("═══════════════════════════════════════════")

    # 2.1 Запрос сброса
    r = await client.post(f"{BASE_URL}/auth/forgot-password", json={
        "email": email,
    })
    assert r.status_code == 200
    ok("POST /auth/forgot-password — 200")

    # 2.2 Несуществующий email (тоже 200 — не раскрываем)
    r = await client.post(f"{BASE_URL}/auth/forgot-password", json={
        "email": "ghost@test.com",
    })
    assert r.status_code == 200
    ok("POST /auth/forgot-password с несуществующим email — 200 (не раскрываем)")

    # 2.3 Сброс с неверным токеном
    r = await client.post(f"{BASE_URL}/auth/reset-password", json={
        "token": str(uuid.uuid4()), "password": "NewPass123",
    })
    assert r.status_code == 400
    ok("POST /auth/reset-password с неверным токеном — 400")


async def test_ticket_flow(client: httpx.AsyncClient, token: str):
    print("\n═══════════════════════════════════════════")
    print("3. ЗАЯВКИ")
    print("═══════════════════════════════════════════")

    headers = {"Authorization": f"Bearer {token}"}

    # Минимальный PNG
    import struct
    import zlib
    def mini_png():
        def chunk(t, d):
            raw = t + d
            return struct.pack(">I", len(d)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)
        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        idat = zlib.compress(b"\x00\xff\x00\x00")
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

    png_bytes = mini_png()

    # 3.1 Создание заявки без фото — должно падать с 422 (field required)
    r = await client.post(f"{BASE_URL}/tickets",
        data={"title": "No photo", "description": "Test without photo"},
        headers=headers,
    )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    ok("Создание заявки без фото — 422 (files required)")

    # 3.2 Создание заявки с 1 фото
    r = await client.post(f"{BASE_URL}/tickets",
        data={"title": "Яма на дороге", "description": "Глубокая яма, нужен ремонт", "address": "ул. Ленина, 15"},
        files=[("files", ("photo1.png", png_bytes, "image/png"))],
        headers=headers,
    )
    assert r.status_code == 201, f"Create ticket failed: {r.text}"
    ticket1 = r.json()
    assert ticket1["title"] == "Яма на дороге"
    assert ticket1["status"] == "NEW"
    assert len(ticket1.get("files", [])) >= 1, f"Files not attached: {ticket1}"
    ok(f"Создание заявки с фото — 201, files={len(ticket1['files'])}")

    # 3.3 Создание заявки с 3 фото
    r = await client.post(f"{BASE_URL}/tickets",
        data={"title": "Сломанная скамейка", "description": "В парке сломана скамейка"},
        files=[
            ("files", ("p1.png", png_bytes, "image/png")),
            ("files", ("p2.png", png_bytes, "image/png")),
            ("files", ("p3.png", png_bytes, "image/png")),
        ],
        headers=headers,
    )
    assert r.status_code == 201, f"Create multi-photo failed: {r.text}"
    ticket2 = r.json()
    assert len(ticket2["files"]) == 3
    ok(f"Создание заявки с 3 фото — 201, files={len(ticket2['files'])}")

    # 3.4 Список заявок
    r = await client.get(f"{BASE_URL}/tickets", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) >= 2
    assert data["total"] >= 2
    ok(f"Список заявок — 200, total={data['total']}")

    # 3.5 Детали заявки
    r = await client.get(f"{BASE_URL}/tickets/{ticket1['id']}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["title"] == "Яма на дороге"
    assert "files" in detail
    assert "comments" in detail
    ok(f"Детали заявки — 200, files={len(detail['files'])}, comments={len(detail['comments'])}")

    # 3.6 Детали несуществующей заявки
    r = await client.get(
        f"{BASE_URL}/tickets/{uuid.uuid4()}", headers=headers,
    )
    assert r.status_code == 404
    ok("Детали несуществующей заявки — 404")

    return ticket1, ticket2


async def test_admin_flow(client: httpx.AsyncClient):
    print("\n═══════════════════════════════════════════")
    print("4. АДМИНИСТРИРОВАНИЕ")
    print("═══════════════════════════════════════════")

    # Сбрасываем Redis, чтобы регистрация админа не попала под rate limit
    await flush_redis()

    # Сначала создаём админа через прямой вызов API
    admin_email = f"admin-{uuid.uuid4().hex[:8]}@test.com"
    r = await client.post(f"{BASE_URL}/auth/register", json={
        "name": "Главный Админ", "email": admin_email, "password": "AdminPass1",
    })
    assert r.status_code == 201, f"Admin register failed: {r.status_code}: {r.text}"
    admin_id = r.json()["id"]

    # Логинимся
    r = await client.post(f"{BASE_URL}/auth/login", json={
        "email": admin_email, "password": "AdminPass1",
    })
    assert r.status_code == 200
    admin_token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Повышаем до админа через прямой SQL (единственный способ без второго админа)
    # Но сначала проверим, что обычный пользователь не может зайти в админку
    # (это уже проверено через require_role)

    # Назначим админа через прямое обновление БД
    # Используем отдельное подключение к БД
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy import text

    db_url = "postgresql+asyncpg://cityboost:cityboost_secret@db:5432/cityboost"
    engine = create_async_engine(db_url)
    async with AsyncSession(engine) as session:
        await session.execute(
            text("UPDATE users SET role = 'ADMIN' WHERE id = :id"),
            {"id": admin_id},
        )
        await session.commit()
    await engine.dispose()

    # Журнал
    ok(f"Пользователь {admin_id} повышен до админа через БД")

    # 4.1 Список пользователей (админ)
    r = await client.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert len(users) >= 2
    ok(f"Список пользователей (админ) — 200, {len(users)} пользователей")

    # 4.2 Смена роли пользователю
    # Найдём обычного пользователя
    user_to_promote = [u for u in users if u["role"] == "user"]
    if user_to_promote:
        target = user_to_promote[0]
        r = await client.patch(
            f"{BASE_URL}/admin/users/{target['id']}/role?new_role=admin",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["role"] == "admin"
        ok(f"Смена роли пользователю — 200, новая роль: admin")

        # Возвращаем обратно
        r = await client.patch(
            f"{BASE_URL}/admin/users/{target['id']}/role?new_role=user",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["role"] == "user"
        ok(f"Смена роли обратно на user — 200")

    # 4.3 Бан пользователя
    user_to_ban = [u for u in users if u["role"] == "user" and u["id"] != admin_id]
    if user_to_ban:
        target = user_to_ban[0]
        r = await client.patch(
            f"{BASE_URL}/admin/users/{target['id']}/ban",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_banned"] is True
        ok(f"Бан пользователя — 200, is_banned=True")

        # Повторный бан (уже забанен)
        r = await client.patch(
            f"{BASE_URL}/admin/users/{target['id']}/ban",
            headers=admin_headers,
        )
        assert r.status_code == 400
        ok("Повторный бан — 400 (уже забанен)")

        # Разбан
        r = await client.patch(
            f"{BASE_URL}/admin/users/{target['id']}/unban",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_banned"] is False
        ok(f"Разбан пользователя — 200, is_banned=False")

        # Повторный разбан
        r = await client.patch(
            f"{BASE_URL}/admin/users/{target['id']}/unban",
            headers=admin_headers,
        )
        assert r.status_code == 400
        ok("Повторный разбан — 400 (не забанен)")

    # 4.4 Нельзя забанить/снять админа с себя
    r = await client.patch(
        f"{BASE_URL}/admin/users/{admin_id}/ban",
        headers=admin_headers,
    )
    assert r.status_code == 400
    ok("Бан самого себя — 400")

    r = await client.patch(
        f"{BASE_URL}/admin/users/{admin_id}/role?new_role=user",
        headers=admin_headers,
    )
    assert r.status_code == 400
    ok("Снять админа с себя — 400")

    return admin_headers, admin_id


async def test_admin_tickets(client: httpx.AsyncClient, admin_headers, ticket1_id):
    print("\n═══════════════════════════════════════════")
    print("5. АДМИНИСТРИРОВАНИЕ ЗАЯВОК")
    print("═══════════════════════════════════════════")

    # 5.1 Список всех заявок
    r = await client.get(f"{BASE_URL}/admin/tickets", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2
    ok(f"Список всех заявок (админ) — 200, всего={data['total']}")

    # 5.2 Фильтрация по статусу
    r = await client.get(f"{BASE_URL}/admin/tickets?status=NEW", headers=admin_headers)
    assert r.status_code == 200
    ok("Фильтрация заявок по статусу — 200")

    # 5.3 Детали заявки (админ)
    r = await client.get(f"{BASE_URL}/admin/tickets/{ticket1_id}", headers=admin_headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["title"]
    ok(f"Детали заявки (админ) — 200, статус={detail['status']}")

    # 5.4 Назначение заявки
    r = await client.patch(
        f"{BASE_URL}/admin/tickets/{ticket1_id}/assign",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] in ("IN_WORK", "NEW")
    ok(f"Назначение заявки — 200, статус после={r.json()['status']}")

    # 5.5 Изменение статуса
    r = await client.patch(
        f"{BASE_URL}/admin/tickets/{ticket1_id}/status?new_status=DONE",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "DONE"
    ok("Изменение статуса на DONE — 200")

    # 5.6 Комментарий
    r = await client.post(
        f"{BASE_URL}/admin/tickets/{ticket1_id}/comments",
        json={"comment_text": "Заявка выполнена, яма заделана"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    ok("Добавление комментария — 201")

    # 5.7 История
    r = await client.get(
        f"{BASE_URL}/admin/tickets/{ticket1_id}/history",
        headers=admin_headers,
    )
    assert r.status_code == 200
    history = r.json()
    assert len(history) >= 1
    ok(f"История заявки — 200, {len(history)} записей")

    # 5.8 Несуществующая заявка (админ)
    r = await client.get(
        f"{BASE_URL}/admin/tickets/{uuid.uuid4()}",
        headers=admin_headers,
    )
    assert r.status_code == 404
    ok("Детали несуществующей заявки (админ) — 404")


async def test_audit_log(client: httpx.AsyncClient, admin_headers):
    print("\n═══════════════════════════════════════════")
    print("6. АУДИТ-ЛОГ")
    print("═══════════════════════════════════════════")

    # 6.1 Получение аудит-лога
    r = await client.get(f"{BASE_URL}/admin/audit-logs", headers=admin_headers)
    assert r.status_code == 200, f"Audit log failed: {r.text}"
    data = r.json()
    assert isinstance(data["items"], list)
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    ok(f"Аудит-лог — 200, всего={data['total']}, items={len(data['items'])}")

    # Проверяем структуру записи
    if data["items"]:
        entry = data["items"][0]
        assert "id" in entry
        assert "admin_id" in entry
        assert "action" in entry
        assert "target_type" in entry
        assert "created_at" in entry
        ok(f"Структура записи аудит-лога валидна (action={entry['action']})")

    # 6.2 Фильтрация по действию
    r = await client.get(
        f"{BASE_URL}/admin/audit-logs?action=ban",
        headers=admin_headers,
    )
    assert r.status_code == 200
    ok("Фильтрация аудит-лога по action=ban — 200")

    # 6.3 Фильтрация по типу цели
    r = await client.get(
        f"{BASE_URL}/admin/audit-logs?target_type=user",
        headers=admin_headers,
    )
    assert r.status_code == 200
    ok("Фильтрация аудит-лога по target_type=user — 200")

    # 6.4 Пагинация
    r = await client.get(
        f"{BASE_URL}/admin/audit-logs?page=1&page_size=5",
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 5
    ok("Пагинация аудит-лога (page_size=5) — 200")


async def test_errors_validation(client: httpx.AsyncClient):
    print("\n═══════════════════════════════════════════")
    print("7. ОШИБКИ И ВАЛИДАЦИЯ")
    print("═══════════════════════════════════════════")

    # 7.1 404
    r = await client.get(f"{BASE_URL}/nonexistent")
    assert r.status_code in (404,)
    ok("Несуществующий маршрут — 404")

    # 7.2 Доступ без токена — 401 (get_current_user проверяет раньше)
    r = await client.get(f"{BASE_URL}/admin/audit-logs")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"
    ok("Аудит-лог без токена — 401")

    # 7.3 Healthcheck
    r = await client.get(f"{BASE_URL.replace('/api/v1', '')}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    ok("Healthcheck — 200, status=ok")


async def flush_redis():
    """Сбросить Redis rate limit counters перед тестом."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url("redis://redis:6379/0", decode_responses=True)
        await r.flushall()
        await r.aclose()
        print("  ✅ Redis сброшен")
    except Exception as e:
        print(f"  ⚠️ Не удалось сбросить Redis: {e}")


async def wait_for_backend(client: httpx.AsyncClient):
    """Ждём, пока backend станет доступен (с ретраями)."""
    for i in range(30):
        try:
            r = await client.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5.0)
            if r.status_code == 200:
                print(f"  ✅ Backend готов (попытка {i+1})")
                return
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        await asyncio.sleep(1)
    print("  ❌ Backend не ответил после 30 попыток")
    sys.exit(1)


async def main():
    await flush_redis()
    async with httpx.AsyncClient(timeout=30.0) as client:
        await wait_for_backend(client)
        email, password, token, headers = await test_auth_flow(client)
        await test_forgot_reset(client, email)
        ticket1, ticket2 = await test_ticket_flow(client, token)
        admin_headers, admin_id = await test_admin_flow(client)
        await test_admin_tickets(client, admin_headers, ticket1["id"])
        await test_audit_log(client, admin_headers)
        await test_errors_validation(client)

    print("\n═══════════════════════════════════════════")
    print(f"ИТОГО: ✅ {passed} тестов пройдено, ❌ {failed} тестов провалено")
    print("═══════════════════════════════════════════")

    return 1 if failed else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
