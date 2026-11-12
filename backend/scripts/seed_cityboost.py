"""Полный сброс и засев демонстрационных данных CityBoost.

Скрипт удаляет ВСЕ данные из основных таблиц (заявки, пользователи, история,
комментарии, файлы, аудит-лог) и создаёт реалистичный набор:

* один администратор (email задаётся в ``ADMIN_EMAIL`` ниже);
* 75–100 обычных пользователей;
* 200–250 заявок по разным районам Витебска за последние 90 дней;
* историю статусов, комментарии и аудит-лог, чтобы аналитика и кабинет
  администратора выглядели правдоподобно.

Запуск внутри backend-контейнера:
    docker compose exec backend python scripts/seed_cityboost.py
"""

from __future__ import annotations

import argparse
import asyncio
import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, text

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
    TicketHistory,
    TicketStatus,
)

# ---------------------------------------------------------------------------
# Параметры демо-данных
# ---------------------------------------------------------------------------

ADMIN_EMAIL = "admin@example.com"
ADMIN_NAME = "Кирилл"
ADMIN_PASSWORD = "CityBoost2026!"

USER_PASSWORD = "UserPass123"
USER_COUNT = 85
TICKET_COUNT = 230
DAYS = 90
EMAIL_DOMAIN = "cityboost.local"

STATUS_LABELS = {
    TicketStatus.NEW: "Новая",
    TicketStatus.IN_WORK: "В работе",
    TicketStatus.DONE: "Выполнена",
    TicketStatus.CLOSED: "Отклонена",
}

# ---------------------------------------------------------------------------
# Справочники
# ---------------------------------------------------------------------------

MALE_NAMES = [
    "Алексей", "Андрей", "Артём", "Владимир", "Денис", "Дмитрий", "Евгений",
    "Игорь", "Кирилл", "Максим", "Михаил", "Николай", "Павел", "Роман",
    "Сергей", "Степан", "Тимофей", "Фёдор", "Юрий", "Ярослав",
]

FEMALE_NAMES = [
    "Алина", "Анна", "Валентина", "Вероника", "Екатерина", "Елена", "Ирина",
    "Ксения", "Марина", "Мария", "Наталья", "Ольга", "Полина", "Светлана",
    "Татьяна", "Юлия", "Яна", "Дарья", "Виктория", "София",
]

LAST_NAMES = [
    "Иванов", "Петров", "Смирнов", "Кузнецов", "Соколов", "Попов", "Лебедев",
    "Козлов", "Новиков", "Морозов", "Волков", "Соловьёв", "Васильев",
    "Зайцев", "Павлов", "Семёнов", "Голубев", "Виноградов", "Богданов",
    "Воробьёв", "Фёдоров", "Михайлов", "Беляев", "Тарасов", "Белов",
    "Комаров", "Орлов", "Киселёв", "Макаров", "Андреев",
]

# Улицы Витебска и примерные координаты. Набор охватывает центр,
# Задвинье, Марково, Билево, Юрьеву Горку, Тирасполь и северные районы.
STREETS: list[tuple[str, float, float]] = [
    ("ул. Ленина", 55.1955, 30.2050),
    ("ул. Замковая", 55.1945, 30.2030),
    ("пр-т Фрунзе", 55.1965, 30.2150),
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
    ("пр-т Московский", 55.1840, 30.2550),
    ("пр-т Строителей", 55.1830, 30.2450),
    ("ул. Титова", 55.1800, 30.2500),
    ("ул. Максима Горького", 55.1910, 30.1980),
    ("ул. Лазо", 55.1880, 30.2220),
    ("ул. 39-й Армии", 55.1890, 30.2320),
    ("ул. Генерала Белобородова", 55.1760, 30.2350),
    ("ул. Воинов-Интернационалистов", 55.1790, 30.2430),
    ("пр-т Победы", 55.2020, 30.2350),
    ("ул. Богатырёва", 55.2010, 30.1980),
    ("ул. Двинская", 55.1970, 30.1880),
    ("ул. Зеньковой", 55.1760, 30.2050),
    ("ул. Железнодорожная", 55.1810, 30.1930),
    ("ул. Калинина", 55.1860, 30.1880),
    ("ул. Ленинградская", 55.1940, 30.2280),
    ("ул. Мира", 55.2050, 30.2150),
    ("ул. Правды", 55.1930, 30.2210),
    ("ул. Чапаева", 55.1960, 30.2120),
    ("ул. Щербакова-Набережная", 55.1920, 30.2010),
    ("ул. Ильинского", 55.1990, 30.2090),
    ("ул. Карла Маркса", 55.1935, 30.2075),
    ("ул. Суворова", 55.1968, 30.2045),
    ("ул. Урицкого", 55.1915, 30.2060),
    ("ул. Вокзальная", 55.1805, 30.1985),
    ("ул. Лучосская", 55.2180, 30.2550),
    ("ул. Северная", 55.2350, 30.2050),
    ("ул. Западная", 55.2010, 30.1480),
    ("ул. Билево", 55.2020, 30.1550),
    ("ул. Юрьева Горка", 55.1720, 30.2020),
    ("ул. Тираспольская", 55.2130, 30.2420),
    ("ул. Садовая", 55.2100, 30.2300),
]

PROBLEMS: list[tuple[str, str]] = [
    ("Яма на дороге", "На проезжей части глубокая яма, мешает движению транспорта."),
    ("Не горит фонарь", "На улице несколько дней не работает уличное освещение."),
    ("Незаконная свалка", "На пустыре образовалась стихийная свалка мусора."),
    ("Повреждена детская площадка", "Сломаны качели и повреждено ограждение площадки."),
    ("Не убран снег", "Тротуар не очищен от снега и наледи, сложно пройти."),
    ("Сломан светофор", "Светофор не переключает сигналы, водители едут на свой риск."),
    ("Протекает крыша", "В подъезде протекает кровля после дождя."),
    ("Брошенный автомобиль", "Во дворе много месяцев стоит брошенный автомобиль."),
    ("Затоплен подвал", "Подвал жилого дома затоплен водой."),
    ("Повреждён тротуар", "На тротуаре провалилась плитка, можно споткнуться."),
    ("Переполнена контейнерная площадка", "Мусор не вывозят несколько дней, контейнеры переполнены."),
    ("Нет горячей воды", "В доме отключена горячая вода без предупреждения."),
    ("Обрушилось дерево", "После ветра дерево упало на пешеходную дорожку."),
    ("Разбито окно в подъезде", "В подъезде разбито окно, зимой холодно."),
    ("Не работает лифт", "Лифт в подъезде не работает уже второй день."),
    ("Открытый люк", "На тротуаре открыт канализационный люк."),
    ("Порвана дорожная разметка", "Пешеходный переход почти не виден из-за стёртой разметки."),
    ("Шумная стройка ночью", "Стройка во дворе продолжается после 23:00."),
]

CLOSE_REASONS = [
    "Спам или реклама",
    "Дубликат уже существующей заявки",
    "Не относится к городским службам",
    "Недостаточно информации, автор не отвечает",
    "Проблема уже устранена до приезда исполнителя",
]

USER_COMMENTS = [
    "Добрый день! Проблема до сих пор актуальна, подскажите сроки.",
    "Прикладываю дополнительные фото по запросу.",
    "Когда планируется устранить проблему? Спасибо.",
    "Сегодня ситуация стала хуже, прошу ускорить.",
]

ADMIN_COMMENTS = [
    "Заявка принята в работу, исполнитель выехал на место.",
    "Спасибо за обращение, работы запланированы на ближайшие дни.",
    "Уточните, пожалуйста, номер подъезда и контактный телефон.",
    "Передали информацию профильной службе, держим на контроле.",
]


# ---------------------------------------------------------------------------
# Генерация данных
# ---------------------------------------------------------------------------


def _status_for_age(age_days: float) -> TicketStatus:
    """Чем старше заявка, тем выше шанс, что её уже выполнили."""
    if age_days < 2:
        weights = (60, 30, 6, 4)
    elif age_days < 7:
        weights = (22, 28, 45, 5)
    elif age_days < 15:
        weights = (8, 20, 67, 5)
    elif age_days < 30:
        weights = (4, 12, 78, 6)
    else:
        weights = (3, 7, 82, 8)
    return random.choices(
        (
            TicketStatus.NEW,
            TicketStatus.IN_WORK,
            TicketStatus.DONE,
            TicketStatus.CLOSED,
        ),
        weights=weights,
    )[0]


def _make_created_at(now: datetime, offset_days: int) -> datetime:
    """Случайное время создания внутри конкретного дня."""
    day = now.date() - timedelta(days=offset_days)
    hour = random.choices(
        range(7, 22),
        weights=[1, 2, 4, 6, 8, 9, 9, 8, 8, 9, 8, 8, 7, 6, 5],
    )[0]
    created = datetime.combine(
        day,
        datetime.min.time(),
        tzinfo=UTC,
    ) + timedelta(
        hours=hour,
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    # Не создаём заявки в будущем.
    return min(created, now - timedelta(minutes=5))


def _resolution_time(created: datetime, age_hours: float) -> datetime:
    """Правдоподобное время выполнения заявки."""
    roll = random.random()
    if roll < 0.15:
        hours = random.uniform(0.7, 4)
    elif roll < 0.75:
        hours = random.uniform(4, 48)
    elif roll < 0.95:
        hours = random.uniform(48, 96)
    else:
        hours = random.uniform(96, 168)
    hours = min(hours, max(0.5, age_hours * 0.95))
    return created + timedelta(hours=hours)


def _assignment_time(created: datetime, upper: datetime, age_hours: float) -> datetime:
    """Время назначения исполнителя: от нескольких минут до суток."""
    max_hours = max(0.05, min(24.0, age_hours * 0.5))
    min_hours = min(0.15, max_hours)
    assigned = created + timedelta(hours=random.uniform(min_hours, max_hours))
    return min(assigned, upper)


def _clamp(value: datetime, minimum: datetime, maximum: datetime) -> datetime:
    return min(max(value, minimum), maximum)


def _build_names(count: int) -> list[str]:
    """Сгенерировать count уникальных русских имён и фамилий."""
    names: list[str] = []
    seen: set[str] = set()
    while len(names) < count:
        first = random.choice(MALE_NAMES + FEMALE_NAMES)
        last = random.choice(LAST_NAMES)
        # Для женских имён фамилия склоняется: Иванов -> Иванова.
        if first in FEMALE_NAMES and not last.endswith("а"):
            last = f"{last}а"
        full = f"{first} {last}"
        if full not in seen:
            seen.add(full)
            names.append(full)
    return names


async def wipe_all_data(db) -> None:
    """Полностью очистить все таблицы приложения, сохранив схему."""
    await db.execute(
        text(
            "TRUNCATE TABLE ticket_files, ticket_comments, ticket_history, "
            "admin_action_log, tickets, users RESTART IDENTITY CASCADE",
        ),
    )
    await db.commit()
    print("Все данные из базы удалены.")


async def seed(
    ticket_count: int = TICKET_COUNT,
    user_count: int = USER_COUNT,
    days: int = DAYS,
    seed_value: int = 2026,
) -> None:
    random.seed(seed_value)
    now = datetime.now(UTC)
    today = now.date()

    async with async_session_factory() as db:
        await wipe_all_data(db)

        admin_password_hash = AuthService.hash_password(ADMIN_PASSWORD)
        user_password_hash = AuthService.hash_password(USER_PASSWORD)

        admin = User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=admin_password_hash,
            role=UserRole.ADMIN,
            is_verified=True,
            is_banned=False,
            created_at=now - timedelta(days=400),
        )

        names = _build_names(user_count)
        users: list[User] = []
        for index, name in enumerate(names, start=1):
            users.append(
                User(
                    name=name,
                    email=f"user{index:03d}@{EMAIL_DOMAIN}",
                    password_hash=user_password_hash,
                    role=UserRole.USER,
                    is_verified=True,
                    is_banned=False,
                    created_at=now - timedelta(
                        days=random.uniform(5, 400),
                        hours=random.uniform(0, 23),
                    ),
                ),
            )

        db.add(admin)
        db.add_all(users)
        await db.flush()

        # ---- Дни создания заявок -----------------------------------------
        # Один гарантированный заказ на каждый из последних days дней,
        # остальные распределены с учётом будней/выходных.
        offsets = list(range(days))
        extra = max(0, ticket_count - days)
        weights = []
        for offset in offsets:
            day = today - timedelta(days=offset)
            weekend = 0.55 if day.weekday() >= 5 else 1.0
            growth = 0.75 + 0.5 * (days - offset) / days
            weights.append(weekend * growth)
        offsets += random.choices(offsets, weights=weights, k=extra)
        random.shuffle(offsets)
        offsets = offsets[:ticket_count]

        tickets: list[Ticket] = []
        history: list[TicketHistory] = []
        comments: list[TicketComment] = []
        audit: list[AdminActionLog] = []

        for offset in offsets:
            created_at = _make_created_at(now, offset)
            age_hours = max(0.1, (now - created_at).total_seconds() / 3600)
            age_days = age_hours / 24
            status = _status_for_age(age_days)

            # Автор должен быть зарегистрирован до создания заявки.
            eligible = [user for user in users if user.created_at <= created_at]
            author = random.choice(eligible) if eligible else min(
                users, key=lambda user: user.created_at,
            )

            title, description = random.choice(PROBLEMS)
            street, base_lat, base_lng = random.choice(STREETS)
            house = random.randint(1, 120)
            latitude = _clamp_float(
                base_lat + random.uniform(-0.004, 0.004),
                VITEBSK_LAT_MIN,
                VITEBSK_LAT_MAX,
            )
            longitude = _clamp_float(
                base_lng + random.uniform(-0.006, 0.006),
                VITEBSK_LNG_MIN,
                VITEBSK_LNG_MAX,
            )

            assigned = status != TicketStatus.NEW
            updated_at = created_at
            assigned_at: datetime | None = None
            finished_at: datetime | None = None

            if status == TicketStatus.DONE:
                finished_at = _resolution_time(created_at, age_hours)
                assigned_at = _assignment_time(created_at, finished_at, age_hours)
                updated_at = finished_at
            elif status == TicketStatus.CLOSED:
                finished_at = min(
                    now,
                    created_at
                    + timedelta(hours=random.uniform(0.5, min(72.0, age_hours * 0.9))),
                )
                assigned_at = _assignment_time(created_at, finished_at, age_hours)
                updated_at = finished_at
            elif status == TicketStatus.IN_WORK:
                assigned_at = _assignment_time(
                    created_at,
                    now,
                    age_hours,
                )
                # Исполнитель недавно касался заявки.
                updated_at = max(
                    assigned_at,
                    now - timedelta(hours=random.uniform(0, 72)),
                )

            ticket = Ticket(
                id=uuid.uuid4(),
                user_id=author.id,
                assigned_to=admin.id if assigned else None,
                title=f"{title} — {street}",
                description=description,
                status=status,
                latitude=latitude,
                longitude=longitude,
                address=f"г. Витебск, {street}, д. {house}",
                close_reason=(
                    random.choice(CLOSE_REASONS)
                    if status == TicketStatus.CLOSED
                    else None
                ),
                notify_author=True,
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

            if assigned and assigned_at is not None:
                history.append(
                    TicketHistory(
                        ticket=ticket,
                        changed_by=admin.id,
                        action="ASSIGNED",
                        old_status=TicketStatus.NEW.value,
                        new_status=TicketStatus.IN_WORK.value,
                        details=f"Заявка назначена на администратора {ADMIN_NAME}",
                        created_at=assigned_at,
                    ),
                )
                audit.append(
                    AdminActionLog(
                        admin_id=admin.id,
                        action="assign_ticket",
                        target_type="ticket",
                        target_id=ticket.id,
                        target_name=ticket.title,
                        details=f"Заявка назначена на администратора {ADMIN_NAME}",
                        created_at=assigned_at,
                    ),
                )

            if status in (TicketStatus.DONE, TicketStatus.CLOSED) and finished_at:
                old_status = (
                    TicketStatus.IN_WORK.value
                    if assigned
                    else TicketStatus.NEW.value
                )
                history.append(
                    TicketHistory(
                        ticket=ticket,
                        changed_by=admin.id,
                        action="STATUS_CHANGED",
                        old_status=old_status,
                        new_status=status.value,
                        details=(
                            f"Статус изменён с «{STATUS_LABELS[TicketStatus.IN_WORK if assigned else TicketStatus.NEW]}» "
                            f"на «{STATUS_LABELS[status]}»"
                            + (
                                f". Причина отклонения: {ticket.close_reason}"
                                if status == TicketStatus.CLOSED
                                else ""
                            )
                        ),
                        created_at=finished_at,
                    ),
                )
                audit.append(
                    AdminActionLog(
                        admin_id=admin.id,
                        action="change_ticket_status",
                        target_type="ticket",
                        target_id=ticket.id,
                        target_name=ticket.title,
                        details=(
                            f"Статус заявки изменён на «{STATUS_LABELS[status]}»"
                            + (
                                f". Причина: {ticket.close_reason}"
                                if status == TicketStatus.CLOSED
                                else ""
                            )
                        ),
                        created_at=finished_at,
                    ),
                )

            # ---- Сообщения в заявке (примерно у каждой четвёртой) ---------
            if status != TicketStatus.NEW and random.random() < 0.25:
                comment_author = author if random.random() < 0.55 else admin
                text_value = random.choice(
                    USER_COMMENTS if comment_author is author else ADMIN_COMMENTS,
                )
                comment_at = _clamp(
                    created_at + timedelta(hours=random.uniform(1, max(2, age_hours * 0.6))),
                    created_at + timedelta(minutes=10),
                    updated_at,
                )
                comments.append(
                    TicketComment(
                        ticket=ticket,
                        author_id=comment_author.id,
                        comment_text=text_value,
                        created_at=comment_at,
                    ),
                )
                history.append(
                    TicketHistory(
                        ticket=ticket,
                        changed_by=comment_author.id,
                        action="COMMENT_ADDED",
                        old_status=None,
                        new_status=status.value,
                        details="Добавлено сообщение",
                        created_at=comment_at,
                    ),
                )

        db.add_all(tickets)
        await db.flush()
        db.add_all(history)
        db.add_all(comments)
        db.add_all(audit)
        await db.commit()

        await _print_summary(db, admin, user_count, ticket_count, days)


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


async def _print_summary(
    db,
    admin: User,
    user_count: int,
    ticket_count: int,
    days: int,
) -> None:
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_tickets = await db.scalar(select(func.count()).select_from(Ticket))
    status_rows = (
        await db.execute(
            select(Ticket.status, func.count()).group_by(Ticket.status),
        )
    ).all()
    date_rows = (
        await db.execute(
            select(
                func.min(Ticket.created_at),
                func.max(Ticket.created_at),
            ),
        )
    ).one()
    queue = await db.scalar(
        select(func.count())
        .select_from(Ticket)
        .where(Ticket.status == TicketStatus.NEW, Ticket.assigned_to.is_(None)),
    )
    done_count = next(
        (count for status, count in status_rows if status == TicketStatus.DONE),
        0,
    )
    total_for_rate = sum(count for _, count in status_rows) or 1

    print()
    print("Демо-данные CityBoost созданы.")
    print(f"  Пользователей всего: {total_users} (обычных: {user_count})")
    print(f"  Заявок всего: {total_tickets} за последние {days} дней")
    print(f"  Период заявок: {date_rows[0]:%d.%m.%Y} — {date_rows[1]:%d.%m.%Y}")
    print("  По статусам:")
    for status, count in sorted(status_rows, key=lambda row: row[0].value):
        print(f"    {status.value}: {count}")
    print(f"  Очередь без исполнителя: {queue or 0}")
    print(f"  Доля выполненных: {round(done_count / total_for_rate * 100, 1)}%")
    print()
    print(f"  Администратор: {ADMIN_EMAIL}")
    print(f"  Пароль администратора: {ADMIN_PASSWORD}")
    print(f"  Пароль пользователей: {USER_PASSWORD}")
    print(f"  Пример пользователя: user001@{EMAIL_DOMAIN}")
    print()
    print("  Вход администратора защищён кодом на email (2FA).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сбросить и засеять данные CityBoost.")
    parser.add_argument(
        "--tickets",
        type=int,
        default=TICKET_COUNT,
        help=f"Сколько заявок создать (200–250, по умолчанию {TICKET_COUNT}).",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=USER_COUNT,
        help=f"Сколько обычных пользователей создать (75–100, по умолчанию {USER_COUNT}).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DAYS,
        help=f"За сколько последних дней распределить заявки (по умолчанию {DAYS}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="Seed генератора случайных чисел (по умолчанию 2026).",
    )
    args = parser.parse_args()
    if not 1 <= args.tickets <= 5000:
        parser.error("--tickets должен быть от 1 до 5000")
    if not 1 <= args.users <= 5000:
        parser.error("--users должен быть от 1 до 5000")
    asyncio.run(
        seed(
            ticket_count=args.tickets,
            user_count=args.users,
            days=args.days,
            seed_value=args.seed,
        ),
    )
