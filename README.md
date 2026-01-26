# Возьмите Клима 🌤️

Production-ready Telegram bot для синхронизации краткосрочных офлайн событий между коллегами (перерывы на курение, кофе, прогулки).

## Возможности

- 👥 **Комнаты (Room)** - группы сотрудников с ролевой моделью (Owner, Admin, Member)
- 🎯 **События** - краткосрочные активности (smoke breaks, coffee, walk, custom)
- 📱 **Участие** - статусы участников (accepted, declined, later, vacation)
- 🌴 **Отпуск** - управление статусом "в отпуске"
- ⏰ **Автозакрытие** - события автоматически закрываются по таймауту
- 📬 **Уведомления** - синхронизированные обновления для всех участников

## Требования

- **Python:** 3.12+
- **Database:** PostgreSQL 15+
- **Async:** asyncio, asyncpg
- **ORM:** SQLAlchemy 2.0 async
- **Bot Framework:** aiogram 3.x

## Быстрый старт

### 1. Клонирование и подготовка

```bash
git clone https://github.com/yourusername/bot_klima.git
cd bot_klima
cp env.example .env
```

### 2. Конфигурация .env

```env
BOT_TOKEN=your_telegram_bot_token_here
POSTGRES_DB=klima
POSTGRES_USER=klima
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql+asyncpg://klima:your_secure_password@localhost:5432/klima
EVENT_CLOSER_INTERVAL_SECONDS=10
```

### 3. Запуск с Docker Compose (рекомендуется)

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL базу данных
- Telegram bot (polling mode)
- Background worker для закрытия событий

### 4. Локальная разработка (без Docker)

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установить зависимости
pip install -e .

# Запустить миграции БД
alembic upgrade head

# Запустить bot
python -m app.bot

# В отдельном терминале - worker
python -m app.worker
```

## Структура проекта

```
bot_klima/
├── app/
│   ├── bot.py                 # Точка входа (polling setup)
│   ├── config.py              # Settings (Pydantic)
│   ├── worker.py              # Background worker (event auto-close)
│   ├── di.py                  # DI container
│   │
│   ├── domain/
│   │   ├── enums/            # EventState, RoomRole, UserGlobalStatus
│   │   └── exceptions/       # Custom exceptions
│   │
│   ├── handlers/
│   │   ├── commands/         # /start, /rooms, /events, /status
│   │   ├── callbacks/        # Button click handlers
│   │   └── middlewares/      # UnitOfWork injection
│   │
│   ├── services/
│   │   ├── events.py         # Event business logic
│   │   ├── rooms.py          # Room management
│   │   ├── access.py         # Role-based access control
│   │   └── notifications.py  # Telegram updates
│   │
│   ├── repositories/
│   │   ├── events.py         # Event data access
│   │   ├── rooms.py          # Room data access
│   │   ├── uow.py            # Unit of Work pattern
│   │   └── db/
│   │       ├── models.py     # SQLAlchemy ORM models
│   │       ├── base.py       # Base model
│   │       └── session.py    # Engine & session factory
│   │
│   └── ui/
│       ├── keyboards.py      # Telegram inline keyboards
│       └── messages.py       # Message templates
│
├── alembic/                   # Database migrations
│   └── versions/
│
├── docker-compose.yml         # Multi-container setup
├── Dockerfile
├── pyproject.toml             # Project dependencies
└── env.example                # Example environment file
```

## Архитектура

Проект следует **многоуровневой архитектуре (Layered Architecture)**:

```
┌─────────────────────────────┐
│  Telegram UI (aiogram)      │  handlers: commands, callbacks
├─────────────────────────────┤
│  Application Services       │  EventService, RoomService, etc.
├─────────────────────────────┤
│  Domain Models              │  Enums, Exceptions, Rules
├─────────────────────────────┤
│  Data Access (Repositories) │  UnitOfWork, ORM wrappers
├─────────────────────────────┤
│  Database (PostgreSQL)      │  SQLAlchemy async
└─────────────────────────────┘
```

**Ключевые принципы:**
- ✅ Event-driven design
- ✅ Clean separation UI ↔ Business Logic
- ✅ Database state source of truth (NO FSM state)
- ✅ Async-only (asyncio + asyncpg)
- ✅ No global state
- ✅ Idempotent operations

## Команды Telegram

### Управление профилем
- `/start` - инициализация бота
- `/status_on` - включить отпуск
- `/status_off` - выключить отпуск

### Комнаты
- `/rooms` - список комнат
- `/create_room <name>` - создать комнату
- `/join_room <room_id>` - присоединиться к комнате

### События
- `/events` - список событий в комнате
- `/create_event <type> [minutes]` - создать событие
  - Types: smoke, coffee, walk, custom
  - Example: `/create_event smoke 15`

## Database Models

### User
```sql
id: int (Telegram ID, PK)
username: str
display_name: str
global_status: ACTIVE | VACATION | DISABLED
vacation_until: datetime (nullable)
```

### Room
```sql
id: UUID (PK)
name: str
owner_id: int (FK User)
state: CREATED | ACTIVE | ARCHIVED
```

### RoomMember
```sql
room_id: UUID (FK)
user_id: int (FK)
role: OWNER | ADMIN | MEMBER
```

### Event
```sql
id: UUID (PK)
room_id: UUID (FK)
creator_id: int (FK User)
type: SMOKE | COFFEE | WALK | CUSTOM
state: CREATED | OPEN | CLOSED
created_at: datetime
close_at: datetime (nullable)
```

### Participation
```sql
user_id: int (FK)
event_id: UUID (FK)
state: PENDING | ACCEPTED | DECLINED | LATER | VACATION
```

## Разработка

### Запуск тестов
```bash
pytest tests/ -v
```

### Код стиль (Ruff)
```bash
ruff check app/
ruff format app/
```

### Type checking (Pyright)
```bash
pyright app/
```

### Миграции БД
```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить на одну версию
alembic downgrade -1
```

## Развертывание

### Production Docker
```bash
docker-compose -f docker-compose.yml up -d
```

### Environment variables
Все чувствительные данные должны быть в `.env` (не коммитить в git):
- `BOT_TOKEN` - токен от @BotFather
- `DATABASE_URL` - полный URL подключения к PostgreSQL
- `POSTGRES_PASSWORD` - пароль БД
- `EVENT_CLOSER_INTERVAL_SECONDS` - интервал polling'а воркера (def: 10)

## Производительность

- ✅ Async-only (no blocking operations)
- ✅ Connection pooling (SQLAlchemy)
- ✅ Batch operations для создания участников
- ✅ Indexed queries для частых операций (room owner, event state)
- ⚠️ Polling mode (можно оптимизировать на long-polling или webhooks)

## Проблемы и TODO

Смотрите [ARCHITECTURE.md](./docs/ARCHITECTURE.md) для подробного анализа слабых мест.

## Contributing

1. Fork проект
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push на branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## License

Проект лицензирован под [MIT License](LICENSE).

## Автор

Создано для команды, которая берет свои климатические паузы всерьез 🌤️

## Поддержка

Нашли баг? [Откройте issue](https://github.com/macentr/bot_klima/issues)

---

**Made with ❤️ using Python 3.12, SQLAlchemy, and aiogram**
