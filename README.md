# Events API Aggregator Service

Backend-сервис-агрегатор для [Events Provider API](http://events-provider.dev-2.python-labs.ru). Кэширует события в PostgreSQL, проксирует регистрации и места к провайдеру.

## Структура API

Роуты вынесены в `app/api/v1/`:

```
app/api/v1/
├── health.py    # GET /api/health
└── router.py    # сборка v1-роутеров
```

Точка входа: `app/main.py` (`create_app`, `lifespan`, middleware).

Интеграция с Events Provider: `app/integrations/events_provider/` (HTTP-клиент, схемы провайдера).

## Endpoints (текущее состояние)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Проверка доступности сервиса |

Swagger UI: `/docs`

## Локальный запуск

```bash
cp .env.example .env
uv sync --group dev
uv run uvicorn app.main:app --reload
```

- Health: http://localhost:8000/api/health
- Docs: http://localhost:8000/docs

## Тесты и линтер

```bash
uv run ruff check .
uv run pytest -q
```

## Переменные окружения

См. `.env.example`. Ключевые группы:

- `LOG_*` — формат и вывод логов
- `POSTGRES_*` — PostgreSQL (шаг 2; на LMS задаёт платформа)
- `EVENTS_PROVIDER_*` — URL и API-ключ провайдера
- `SYNC_CRON_*` — расписание фоновой синхронизации (шаг 6)

**LMS:** для агрегатора в кластере задайте внутренний URL провайдера:

`http://student-system-events-provider-web.student-system-events-provider.svc:8000`

Локально — публичный `http://events-provider.dev-2.python-labs.ru`.

## CI/CD

Push в `main` → GitHub Actions: `ruff` → build образа → deploy на LMS.

Секрет репозитория: `LMS_API_KEY` (только для деплоя, не в `.env` приложения).

## Схема Read-path / write-path

```mermaid
flowchart LR
  Client[Клиент / фронт]
  Agg[Агрегатор]
  DB[(PostgreSQL)]
  Prov[Events Provider API]

  Client -->|GET /api/events| Agg
  Agg -->|SELECT| DB

  Client -->|GET /api/events/id/seats| Agg
  Agg -->|GET seats + кэш 30с| Prov

  Client -->|POST /api/tickets| Agg
  Agg -->|register| Prov
  Agg -->|сохранить билет| DB

  Worker[Фон sync / POST /api/sync/trigger]
  Worker --> Agg
  Agg -->|GET events cursor| Prov
  Agg -->|UPSERT| DB
```
