# AI coding guide for this repo

## Big picture architecture
- Layered async bot: handlers → services → repositories → DB models. See [app/handlers](app/handlers), [app/services](app/services), [app/repositories](app/repositories), [app/repositories/db/models.py](app/repositories/db/models.py).
- Entry points: bot polling in [app/bot.py](app/bot.py), background event closer in [app/worker.py](app/worker.py). `DATABASE_URL` and `BOT_TOKEN` always come from env via `Settings` in [app/config.py](app/config.py).
- DB is the source of truth (no FSM for business state). FSM is only used for short-lived UI flows in [app/handlers/callbacks/menu.py](app/handlers/callbacks/menu.py) and [app/handlers/callbacks/rooms.py](app/handlers/callbacks/rooms.py).

## Data flow & transaction boundaries
- Every Telegram update gets a fresh `UnitOfWork` injected by middleware in [app/handlers/middlewares/uow.py](app/handlers/middlewares/uow.py). Use `async with uow:` and `uow.session` (auto-commit/rollback) as in [app/handlers/commands/events.py](app/handlers/commands/events.py).
- Services enforce business rules (RBAC via `AccessControl`) and orchestrate repos; see [app/services/events.py](app/services/events.py) and [app/services/rooms.py](app/services/rooms.py).

## Project-specific rules & patterns
- One OPEN event per room is enforced by a partial unique index in [app/repositories/db/models.py](app/repositories/db/models.py). The worker closes expired events periodically (no per-event timers) in [app/worker.py](app/worker.py).
- Cooldown: new event can be created only 5 minutes after the previous one (see `EventService.create_event` in [app/services/events.py](app/services/events.py)).
- Notifications are sent only on event creation; participation updates are refreshed on-demand via callbacks (`EventActionCb`), see [app/services/notifications.py](app/services/notifications.py) and [app/handlers/callbacks/events.py](app/handlers/callbacks/events.py).
- “Clean chat” UX: store `last_menu_message_id` and `last_invite_message_id` on users and delete previous messages (see [app/handlers/commands/start.py](app/handlers/commands/start.py) and [app/handlers/callbacks/menu.py](app/handlers/callbacks/menu.py)).
- Inline keyboards and callback routing are centralized in [app/ui/keyboards.py](app/ui/keyboards.py); text templates live in [app/ui/messages.py](app/ui/messages.py).

## Integration points
- External deps: aiogram 3.x, SQLAlchemy 2.x async + asyncpg, Alembic. See [pyproject.toml](pyproject.toml).
- Postgres schema changes go through Alembic migrations in [alembic/versions](alembic/versions).

## Dev workflows (current sources)
- Run via Docker: `docker-compose up -d` (bot + worker + db) in [README.md](README.md).
- Local run: `python -m app.bot` and `python -m app.worker` after `alembic upgrade head` (see [README.md](README.md), [DEVELOPMENT.md](DEVELOPMENT.md)).
- Quality checks: `ruff check app/ --fix`, `ruff format app/`, `pyright app/` (see [README.md](README.md)).
- Tests: `pytest tests/ -v --cov=app` (see [README.md](README.md)).
- **Git workflow:** Все изменения коммитятся и пушатся в git. Никогда не изменяйте код напрямую на prod.
- **Production deployment:** Развертка на prod выполняется только вручную пользователем на удаленной машине через SSH. AI агент не деплоит в продакшн.

## Change tips
- When adding features, keep handlers thin (I/O + parsing), place business rules in services, and use repositories only inside a `UnitOfWork` scope.
- If you change DB models, create/commit Alembic revisions and update constraints consistent with existing partial indexes.
