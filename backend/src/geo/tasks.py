"""
Фоновые задачи геокодирования на базе arq (Redis).

Worker запускается: python -m src.geo.tasks

Сценарии:
  - Пользователь отправил координаты → пытаемся получить адрес.
    Если таймаут → сохраняем заявку, фоновый таск дозапрашивает адрес.
  - Пользователь отправил текстовый адрес → пытаемся получить координаты.
    Если сервис недоступен → повтор с экспоненциальной задержкой.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from arq import Worker
from arq.connections import RedisSettings
from sqlalchemy import select

from src.config import settings
from src.database import async_session_factory
from src.geo.service import GeoClient
from src.tickets.models import Ticket

logger = logging.getLogger("cityboost.geo.tasks")

REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)


async def resolve_address_for_ticket(ctx: dict, ticket_id: str) -> bool:
    """
    Фоновая задача: получить адрес по координатам заявки.

    Вызывается, когда при создании заявки были указаны координаты,
    но геокодер был недоступен (таймаут/ошибка).

    Args:
        ctx: Контекст arq.
        ticket_id: UUID заявки.

    Returns:
        True — адрес получен и сохранён, False — ошибка.
    """
    client = GeoClient()
    ticket_uuid = uuid.UUID(ticket_id)

    try:
        async with async_session_factory() as db:
            result = await db.execute(select(Ticket).where(Ticket.id == ticket_uuid))
            ticket = result.scalar_one_or_none()
            if ticket is None:
                logger.warning("Заявка %s не найдена для обратного геокодирования", ticket_id)
                return False

            geo_result = await client.reverse_geocode(ticket.latitude, ticket.longitude)
            if geo_result and geo_result.address:
                ticket.address = geo_result.address
                await db.commit()
                logger.info("Адрес для заявки %s: %s", ticket_id, geo_result.address)
                return True
            else:
                logger.warning("Не удалось получить адрес для заявки %s", ticket_id)
                return False
    except Exception as exc:
        logger.error("Ошибка обратного геокодирования заявки %s: %s", ticket_id, exc)
        return False
    finally:
        await client.close()


async def resolve_coordinates_for_ticket(ctx: dict, ticket_id: str, attempt: int = 1) -> bool:
    """
    Фоновая задача: получить координаты по текстовому адресу заявки.

    Реализует экспоненциальную задержку при повторных попытках.

    Args:
        ctx: Контекст arq.
        ticket_id: UUID заявки.
        attempt: Номер попытки (начинается с 1).

    Returns:
        True — координаты получены, False — ошибка.
    """
    client = GeoClient()
    ticket_uuid = uuid.UUID(ticket_id)
    MAX_ATTEMPTS = 5

    try:
        async with async_session_factory() as db:
            result = await db.execute(select(Ticket).where(Ticket.id == ticket_uuid))
            ticket = result.scalar_one_or_none()
            if ticket is None:
                logger.warning("Заявка %s не найдена для прямого геокодирования", ticket_id)
                return False

            if ticket.address:
                geo_result = await client.direct_geocode(ticket.address)
                if geo_result:
                    ticket.latitude = geo_result.latitude
                    ticket.longitude = geo_result.longitude
                    await db.commit()
                    logger.info(
                        "Координаты для заявки %s: (%f, %f)",
                        ticket_id, geo_result.latitude, geo_result.longitude,
                    )
                    return True

            # Экспоненциальная задержка перед повторной постановкой
            if attempt < MAX_ATTEMPTS:
                delay = min(2**attempt * 10, 300)  # 20, 40, 80, 160, 300 сек
                logger.info(
                    "Повторная попытка геокодирования заявки %s через %d сек (попытка %d/%d)",
                    ticket_id, delay, attempt, MAX_ATTEMPTS,
                )
                await asyncio.sleep(delay)
                # Повторная постановка задачи через arq
                await ctx["redis"].enqueue_job(
                    resolve_coordinates_for_ticket.__name__,
                    ticket_id,
                    attempt + 1,
                )
                return False
            else:
                logger.warning("Исчерпаны попытки геокодирования для заявки %s", ticket_id)
                return False
    except Exception as exc:
        logger.error("Ошибка прямого геокодирования заявки %s: %s", ticket_id, exc)
        return False
    finally:
        await client.close()


def run_worker() -> None:
    """Запустить воркер arq."""
    worker = Worker(
        [resolve_address_for_ticket, resolve_coordinates_for_ticket],
        redis_settings=REDIS_SETTINGS,
    )
    logger.info("Запуск воркера фоновых задач геокодирования...")
    worker.run()


def main() -> None:
    """Точка входа для запуска воркера."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_worker()


if __name__ == "__main__":
    main()
