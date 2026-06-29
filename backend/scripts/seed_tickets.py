"""
Seed 100 random tickets around Vitebsk.
Creates tickets directly via SQL for speed.
"""

from __future__ import annotations

import asyncio
import random
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://cityboost:cityboost_secret@db:5432/cityboost"

TITLES = [
    "Яма на дороге",
    "Разбитый тротуар",
    "Сломанный фонарь",
    "Не вывозят мусор",
    "Сломанная скамейка",
    "Свалка во дворе",
    "Плохое освещение",
    "Разбитая остановка",
    "Сломанные качели",
    "Не косят траву",
    "Треснувшая труба",
    "Затопленный подвал",
    "Сломанный почтовый ящик",
    "Отсутствует урна",
    "Поваленное дерево",
    "Разбитое окно в подъезде",
    "Не работает лифт",
    "Разбитая детская площадка",
    "Мусор после стройки",
    "Граффити на стене",
    "Провал асфальта",
    "Разбитый светофор",
    "Сломанный пандус",
    "Неисправная дверь в подъезде",
    "Горящий мусорный бак",
]

ADDRESSES = [
    "ул. Ленина, {n}",
    "пр-т Фрунзе, {n}",
    "ул. Гагарина, {n}",
    "ул. Кирова, {n}",
    "пр-т Московский, {n}",
    "ул. Советская, {n}",
    "ул. Пушкина, {n}",
    "ул. Октябрьская, {n}",
    "пр-т Строителей, {n}",
    "ул. Замковая, {n}",
    "ул. Толстого, {n}",
    "ул. Войкова, {n}",
    "ул. Космонавтов, {n}",
    "ул. Будённого, {n}",
    "пр-т Победы, {n}",
    "ул. Чапаева, {n}",
    "ул. Щорса, {n}",
    "ул. Терешковой, {n}",
    "ул. Горького, {n}",
    "ул. Ленинградская, {n}",
]

V_LAT, V_LNG = 55.1904, 30.2049

DESCRIPTIONS = [
    "Требуется срочный ремонт. Жители жалуются.",
    "Проблема существует уже месяц, никак не решат.",
    "Просьба принять меры и устранить неисправность.",
    "Опасно для жителей, особенно детей.",
    "Необходимо вмешательство городских служб.",
    "Обращались в ЖЭУ — без результата.",
    "Требуется замена оборудования.",
    "Ситуация ухудшается с каждым днём.",
    "Просим обратить внимание на эту проблему.",
    "Нужно провести обследование и ремонт.",
]


async def get_first_user_id(engine) -> str:
    """Get the first regular user's ID to assign tickets to them."""
    async with AsyncSession(engine) as session:
        r = await session.execute(
            text("SELECT id FROM users WHERE role = 'USER' ORDER BY created_at ASC LIMIT 1")
        )
        row = r.fetchone()
        if row:
            return row[0]
        # Create a user if none exist
        uid = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO users (id, name, email, password_hash, role, created_at)
                VALUES (:id, :name, :email, :hash, 'USER', :now)
            """),
            {
                "id": uid,
                "name": "Seed User",
                "email": f"seed-{uuid.uuid4().hex[:8]}@test.com",
                "hash": "$2b$12$LJ3m4ys3Lk3w5Qy3m4ys3O3m4ys3Lk3w5Qy3m4ys3O",
                "now": datetime.now(timezone.utc),
            },
        )
        await session.commit()
        return uid


async def main():
    engine = create_async_engine(DB_URL)

    # Verify connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Подключение к БД установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return 1

    user_id = await get_first_user_id(engine)
    print(f"👤 Использую user_id = {user_id}")

    print(f"\n🚀 Создаю 100 заявок через SQL...\n")

    created = 0
    for i in range(100):
        title = random.choice(TITLES)
        desc = random.choice(DESCRIPTIONS)
        addr = random.choice(ADDRESSES).format(n=random.randint(1, 100))
        lat = V_LAT + random.uniform(-0.025, 0.025)
        lng = V_LNG + random.uniform(-0.025, 0.025)

        ticket_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        async with AsyncSession(engine) as session:
            try:
                await session.execute(
                    text("""
                        INSERT INTO tickets (id, user_id, title, description, status, latitude, longitude, address, created_at, updated_at)
                        VALUES (:id, :user_id, :title, :desc, 'NEW', :lat, :lng, :addr, :now, :now)
                    """),
                    {
                        "id": ticket_id,
                        "user_id": user_id,
                        "title": title,
                        "desc": f"{desc} [{addr}]",
                        "lat": lat,
                        "lng": lng,
                        "addr": addr,
                        "now": now,
                    },
                )
                await session.commit()
                created += 1
                print(f"  ✅ [{created:3d}/100] #{str(ticket_id)[:8]} — {title}")
            except Exception as e:
                await session.rollback()
                print(f"  ❌ [{i+1:3d}/100] Ошибка: {e}")

    await engine.dispose()

    print(f"\n✅ Создано {created} заявок!")
    print(f"📊 Всего заявок: SELECT COUNT(*) FROM tickets;")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
