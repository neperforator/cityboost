# Docker команды для CityBoost

> Все команды выполняются из корня проекта (`D:\cb\cityboost`).
> На PowerShell для последовательного выполнения используйте `;` вместо `&&`.

## Запуск проекта

```bash
# Запустить все сервисы в фоне
docker compose up -d

# Пересобрать образы и запустить
docker compose up -d --build

# Пересобрать только бэкенд (без кэша) и запустить
docker compose build --no-cache backend
docker compose up -d
```

## Остановка

```bash
# Остановить все сервисы
docker compose down

# Остановить и удалить volumes (БД, Redis — все данные пропадут)
docker compose down -v
```

## Логи

```bash
# Логи бэкенда (live)
docker compose logs -f backend

# Логи всех сервисов
docker compose logs -f

# Логи определённого сервиса
docker compose logs -f nginx
docker compose logs -f worker
```

## Тесты

```bash
# Запустить все тесты
docker compose run --rm backend pytest tests/ -v

# Запустить конкретный тест-файл
docker compose run --rm backend pytest tests/test_auth.py -v

# Запустить конкретный тест-класс
docker compose run --rm backend pytest tests/test_auth.py::TestRegister -v

# Запустить конкретный тест
docker compose run --rm backend pytest tests/test_auth.py::TestRegister::test_register_success -v

# Пересобрать и запустить тесты (после изменений в коде/тестах)
docker compose build --no-cache backend
docker compose run --rm backend pytest tests/ -v

# Быстрая пересборка (если менялись только зависимости)
docker compose build backend
docker compose run --rm backend pytest tests/ -v
```

## Один сервис

```bash
# Зайти в контейнер бэкенда
docker compose run --rm backend bash

# Зайти в БД
docker compose exec db psql -U cityboost -d cityboost
```

## Порты

| Сервис    | Порт  |
|-----------|-------|
| Бэкенд    | 8000  |
| Nginx     | 80/443 |
| PostgreSQL| 5432  |
| Redis     | 6379  |
