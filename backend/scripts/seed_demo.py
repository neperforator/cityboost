"""Засеять демо-данные для проверки аналитики.

Создаёт несколько администраторов, пользователей и много заявок за последние
120 дней. Скрипт идемпотентен: перед вставкой удаляет предыдущие демо-данные
(пользователи с email вида demo.*@cityboost.local).

Запуск внутри backend-контейнера:
    docker compose exec backend python scripts/seed_demo.py
"""

from __future__ import annotations

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, or_, select

from src.auth.models import User, UserRole
from src.auth.service import AuthService
from src.common.audit import AdminActionLog
from src.database import async_session_factory
from src.tickets.constants import (
    VITEBSK_LAT_MAX,
    VITEBSK_LAT_MIN,
    VITEBSK_LNG_MAX,
    VITEBSK_LNG_MIN,
)
from src.tickets.models import (
    Ticket,
    TicketComment,
    TicketFile,
    TicketHistory,
    TicketStatus,
)

PASSWORD = "DemoPass123"
EMAIL_DOMAIN = "cityboost.local"
ADMIN_COUNT = 8
USER_COUNT = 40
TICKET_COUNT = 1500
DAYS = 120

ADMIN_NAMES = [
    "Анна Смирнова",
    "Дмитрий Орлов",
    "Елена Крылова",
    "Игорь Савельев",
    "Марина Белова",
    "Павел Гусев",
    "Ольга Фомина",
    "Сергей Лебедев",
]

USER_NAMES = [
    "Алексей Иванов",
    "Мария Петрова",
    "Николай Соколов",
    "Татьяна Морозова",
    "Андрей Волков",
    "Екатерина Зайцева",
    "Михаил Павлов",
    "Ирина Семёнова",
    "Владимир Козлов",
    "Наталья Степанова",
    "Денис Николаев",
    "Юлия Андреева",
    "Артём Макаров",
    "Светлана Никитина",
    "Роман Захаров",
    "Ксения Миронова",
    "Евгений Фёдоров",
    "Алина Ковалёва",
    "Максим Тихонов",
    "Вероника Комарова",
]

# Улицы Витебска и их примерные координаты: заявки кластеризуются
# вокруг реальных городских улиц, а не размазываются по всей области.
STREETS = [
    ("ул. Ленина", 55.1955, 30.2050),
    ("ул. Замковая", 55.1945, 30.2030),
    ("пр-т Фрунзе", 55.1965, 30.2100),
    ("ул. Кирова", 55.1920, 30.2080),
    ("ул. Гагарина", 55.1880, 30.2150),
    ("ул. Пушкина", 55.1930, 30.2150),
    ("ул. Советская", 55.1900, 30.2020),
    ("ул. Смоленская", 55.1860, 30.2000),
    ("пр-т Черняховского", 55.1980, 30.2200),
    ("ул. Терешковой", 55.1850, 30.2100),
    ("ул. Космонавтов", 55.1920, 30.2250),
    ("ул. Чкалова", 55.2000, 30.1950),
    ("ул. Димитрова", 55.1870, 30.1950),
    ("ул. Богдана Хмельницкого", 55.1990, 30.1900),
]

PROBLEMS = [
    ("Яма на дороге", "На проезжей части глубокая яма, мешает движению."),
    ("Не горит фонарь", "На улице не работает уличное освещение."),
    ("Незаконная свалка", "На пустыре образовалась стихийная свалка мусора."),
    ("Повреждена детская площадка", "Сломаны качели и ограждение площадки."),
    ("Не убран снег", "Тротуар не очищен от снега и наледи."),
    ("Сломан светофор", "Светофор не переключает сигналы."),
    ("Протекает крыша", "В подъезде протекает кровля после дождя."),
    ("Брошенный автомобиль", "Во дворе стоит брошенный автомобиль."),
    ("Затоплен подвал", "Подвал жилого дома затоплен водой."),
    ("Повреждён тротуар", "На тротуаре провалилась плитка."),
]

REJECTION_REASONS = [
    "Спам или реклама",
    "Дубликат уже существующей заявки",
    "Не относится к городским службам",
    "Недостаточно информации, автор не отвечает",
]


async def clear_demo_data(db) -> None:
    """Удалить предыдущие демо-данные, не трогая реальные записи."""
    demo_ids = list(
        (
            await db.execute(
                select(User.id).where(
                    User.email.like(f"demo.%@{EMAIL_DOMAIN}"),
                ),
            )
        ).scalars(),
    )
    if not demo_ids:
        return

    ticket_filter = or_(
        Ticket.user_id.in_(demo_ids),
        Ticket.assigned_to.in_(demo_ids),
    )
    ticket_ids = select(Ticket.id).where(ticket_filter)

    await db.execute(
        delete(TicketComment).where(TicketComment.ticket_id.in_(ticket_ids)),
    )
    await db.execute(
        delete(TicketHistory).where(TicketHistory.ticket_id.in_(ticket_ids)),
    )
    await db.execute(
        delete(TicketFile).where(TicketFile.ticket_id.in_(ticket_ids)),
    )
    await db.execute(delete(Ticket).where(ticket_filter))
    await db.execute(
        delete(AdminActionLog).where(AdminActionLog.admin_id.in_(demo_ids)),
    )
    await db.execute(delete(User).where(User.id.in_(demo_ids)))
    await db.commit()
    print(f"Удалены предыдущие демо-данные: {len(demo_ids)} пользователей")


async def seed(ticket_count: int = TICKET_COUNT, days: int = DAYS) -> None:
    random.seed(42)
    now = datetime.now(UTC)

    async with async_session_factory() as db:
        await clear_demo_data(db)

        password_hash = AuthService.hash_password(PASSWORD)

        admins = [
            User(
                name=ADMIN_NAMES[index],
                email=f"demo.admin{index + 1:02d}@{EMAIL_DOMAIN}",
                password_hash=password_hash,
                role=UserRole.ADMIN,
                is_verified=True,
                created_at=now - timedelta(days=days + 30),
            )
            for index in range(ADMIN_COUNT)
        ]
        users = [
            User(
                name=USER_NAMES[index % len(USER_NAMES)],
                email=f"demo.user{index + 1:03d}@{EMAIL_DOMAIN}",
                password_hash=password_hash,
                role=UserRole.USER,
                is_verified=True,
                created_at=now - timedelta(days=days + 30),
            )
            for index in range(USER_COUNT)
        ]
        db.add_all(admins + users)
        await db.flush()

        tickets: list[Ticket] = []
        history: list[TicketHistory] = []

        for index in range(1, ticket_count + 1):
            author = random.choice(users)

            # Поток созданий равномерный по всему периоду.
            created_at = now - timedelta(
                days=random.uniform(0, days - 0.01),
                seconds=random.randint(0, 86_399),
            )
            created_at = min(created_at, now)
            age_days = (now - created_at).total_seconds() / 86_400

            # Чем старше заявка, тем выше шанс, что её уже выполнили.
            # CLOSED — редкое отклонение (спам, дубль), а не этап маршрута.
            if age_days < 3:
                weights = (55, 27, 13, 5)
            elif age_days < 10:
                weights = (18, 22, 55, 5)
            elif age_days < 30:
                weights = (6, 8, 81, 5)
            else:
                weights = (1, 2, 92, 5)
            status = random.choices(
                (
                    TicketStatus.NEW,
                    TicketStatus.IN_WORK,
                    TicketStatus.DONE,
                    TicketStatus.CLOSED,
                ),
                weights=weights,
            )[0]

            if status == TicketStatus.DONE:
                # Решение занимает от 30 минут до 5 суток, но не позже «сейчас».
                max_hours = max(0.5, min(120.0, age_days * 24 * 0.95))
                updated_at = min(
                    now,
                    created_at + timedelta(hours=random.uniform(0.5, max_hours)),
                )
            elif status == TicketStatus.CLOSED:
                # Отклоняют обычно быстро — в течение нескольких часов.
                max_hours = max(0.2, min(72.0, age_days * 24 * 0.95))
                updated_at = min(
                    now,
                    created_at + timedelta(hours=random.uniform(0.2, max_hours)),
                )
            elif status == TicketStatus.IN_WORK:
                # Исполнитель недавно касался заявки.
                updated_at = max(
                    created_at,
                    now - timedelta(hours=random.uniform(0, 48)),
                )
            else:
                updated_at = created_at

            if status == TicketStatus.NEW:
                assignee = random.choice(admins) if random.random() < 0.10 else None
            elif status == TicketStatus.IN_WORK:
                assignee = random.choice(admins) if random.random() < 0.9 else None
            elif status == TicketStatus.DONE:
                assignee = random.choice(admins) if random.random() < 0.95 else None
            else:
                assignee = random.choice(admins) if random.random() < 0.3 else None

            title, description = random.choice(PROBLEMS)
            street, base_lat, base_lng = random.choice(STREETS)
            house = random.randint(1, 120)
            latitude = min(
                max(base_lat + random.uniform(-0.004, 0.004), VITEBSK_LAT_MIN),
                VITEBSK_LAT_MAX,
            )
            longitude = min(
                max(base_lng + random.uniform(-0.006, 0.006), VITEBSK_LNG_MIN),
                VITEBSK_LNG_MAX,
            )

            ticket = Ticket(
                user_id=author.id,
                assigned_to=assignee.id if assignee else None,
                title=f"{title} №{index}",
                description=description,
                status=status,
                latitude=latitude,
                longitude=longitude,
                address=f"г. Витебск, {street}, д. {house}",
                close_reason=(
                    random.choice(REJECTION_REASONS)
                    if status == TicketStatus.CLOSED
                    else None
                ),
                created_at=created_at,
                updated_at=updated_at,
            )
            tickets.append(ticket)
            history.append(
                TicketHistory(
                    ticket=ticket,
                    changed_by=author.id,
                    action="CREATED",
                    old_status=None,
                    new_status=TicketStatus.NEW.value,
                    details="Заявка создана",
                    created_at=created_at,
                ),
            )

        db.add_all(tickets)
        await db.flush()
        db.add_all(history)
        await db.commit()

        # ---- Итоговая сводка ----
        total_users = await db.scalar(select(func.count()).select_from(User))
        total_tickets = await db.scalar(select(func.count()).select_from(Ticket))
        status_rows = (
            await db.execute(
                select(Ticket.status, func.count()).group_by(Ticket.status),
            )
        ).all()
        assignee_rows = (
            await db.execute(
                select(User.name, func.count())
                .select_from(Ticket)
                .join(User, Ticket.assigned_to == User.id)
                .group_by(User.name)
                .order_by(func.count().desc()),
            )
        ).all()

        print()
        print("Демо-данные созданы.")
        print(f"  Пользователей всего: {total_users}")
        print(f"  Заявок всего: {total_tickets}")
        print("  По статусам:")
        for status, count in sorted(status_rows, key=lambda row: row[0].value):
            print(f"    {status.value}: {count}")
        print("  Нагрузка по демо-администраторам:")
        for name, count in assignee_rows:
            print(f"    {name}: {count}")
        print()
        print(f"  Пароль демо-пользователей: {PASSWORD}")
        print(f"  Email админов: demo.admin01@{EMAIL_DOMAIN} … "
              f"demo.admin{ADMIN_COUNT:02d}@{EMAIL_DOMAIN}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Засеять демо-данные CityBoost.")
    parser.add_argument(
        "--tickets",
        type=int,
        default=TICKET_COUNT,
        help=f"Сколько заявок создать (по умолчанию {TICKET_COUNT}).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DAYS,
        help=f"За сколько последних дней распределить заявки (по умолчанию {DAYS}).",
    )
    args = parser.parse_args()
    asyncio.run(seed(ticket_count=args.tickets, days=args.days))
