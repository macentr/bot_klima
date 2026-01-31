# Возьмите Клима 🌤️

Production-ready Telegram bot для синхронизации краткосрочных офлайн событий между коллегами (перерывы на курение, кофе, прогулки).

## Возможности

- 👥 **Комнаты (Room)** - группы сотрудников с ролевой моделью (Owner, Admin, Member)
- 🔗 **Инвайт-коды** - простое присоединение к комнатам по уникальному коду
- 🎯 **События** - краткосрочные активности (smoke, coffee, walk, custom с описанием)
- 📱 **Участие** - статусы участников (accepted, declined, later, vacation)
- 🌴 **Отпуск** - управление статусом "в отпуске"
- ⏰ **Автозакрытие** - события автоматически закрываются по таймауту
- 📬 **Уведомления** - синхронизированные обновления для всех участников
- 🔐 **Админ-панель** - специальные команды для администраторов бота
- 🧹 **Умные сообщения** - автоматическая очистка меню и служебных сообщений

## Требования

- **Python:** 3.12+
- **Database:** PostgreSQL 15+
- **Async:** asyncio, asyncpg
- **ORM:** SQLAlchemy 2.0 async
- **Bot Framework:** aiogram 3.x

## Быстрый старт

### 1. Клонирование и подготовка

```bash
git clone https://github.com/macentr/bot_klima.git
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
- `/start` - инициализация бота и отображение главного меню
- `/status_on` - включить отпуск (vacation mode)
- `/status_off` - выключить отпуск

### Комнаты
- `/rooms` - список комнат и меню управления
- `/create_room <name>` - создать новую комнату (вы станете Owner)
- `/join_room <invite_code>` - присоединиться к комнате по инвайт-коду
- `/delete_room <room_id>` - удалить комнату (только для владельца)

### События
- `/events` - список событий в выбранной комнате
- `/create_event <type> [minutes]` - создать событие
  - Types: `smoke`, `coffee`, `walk`, `custom:<описание>`
  - Example: `/create_event smoke 15`
  - Example: `/create_event custom:Обед 30`
  
### Администрирование (только для админов бота)
- `/admin_grant <user_id>` - выдать пользователю админ-права
- `/admin_revoke <user_id>` - забрать админ-права

## Database Models

### User
```sql
id: int (Telegram ID, PK)
username: str | null
display_name: str
global_status: ACTIVE | VACATION | DISABLED
vacation_until: datetime (nullable)
is_admin: bool (default: false)
last_menu_message_id: int (nullable) -- для умной очистки меню
last_invite_message_id: int (nullable) -- для умной очистки инвайтов
```

### Room
```sql
id: UUID (PK)
name: str
invite_code: str (unique, nullable) -- уникальный код для присоединения
open_event_id: UUID (FK Event, nullable) -- текущее открытое событие
owner_id: int (FK User)
state: CREATED | ACTIVE | ARCHIVED
```

### RoomMember
```sql
room_id: UUID (FK, PK)
user_id: int (FK, PK)
role: OWNER | ADMIN | MEMBER
-- Constraint: только один OWNER на комнату
```

### Event
```sql
id: UUID (PK)
room_id: UUID (FK)
creator_id: int (FK User)
type: SMOKE | COFFEE | WALK | CUSTOM
state: CREATED | OPEN | CLOSED
custom_description: str (nullable) -- для custom событий
created_at: datetime
close_at: datetime (nullable)
creator_message_id: int (nullable) -- ID сообщения создателя для обновления
-- Constraint: только одно OPEN событие на комнату
```

### Participation
```sql
event_id: UUID (FK, PK)
user_id: int (FK, PK)
state: ACCEPTED | DECLINED | LATER | VACATION
note: text (nullable)
-- Constraint: уникальное участие пользователя в событии
```

## Миграции базы данных

Проект использует Alembic для управления схемой БД. Последние миграции:
- `0008_add_custom_event_type` - добавление поддержки кастомных событий
- `0007_add_user_is_admin` - флаг админа для пользователей
- `0006_add_user_last_messages` - хранение ID последних сообщений для очистки
- `0005_restore_owner_roles` - исправление ролей владельцев комнат
- `0004_add_open_event_id` - связь комнаты с открытым событием
- `0003_add_invite_code` - система инвайт-кодов

## Разработка

### Запуск тестов
```bash
pytest tests/ -v --cov=app
```

### Код стиль (Ruff)
```bash
ruff check app/ --fix
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

# Посмотреть текущую версию
alembic current

# История миграций
alembic history
```

## Развертывание

### Production Docker
```bash
# Старт всех сервисов (db, bot, worker)
docker-compose up -d

# Проверка логов
docker-compose logs -f bot
docker-compose logs -f worker

# Остановка
docker-compose down
```

### Environment variables
Все чувствительные данные должны быть в `.env` (не коммитить в git):
- `BOT_TOKEN` - токен от @BotFather
- `DATABASE_URL` - полный URL подключения к PostgreSQL
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - параметры БД
- `EVENT_CLOSER_INTERVAL_SECONDS` - интервал polling'а воркера (def: 10)

## Производительность

- ✅ Async-only (no blocking operations)
- ✅ Connection pooling (SQLAlchemy)
- ✅ Batch operations для создания участников
- ✅ Indexed queries для частых операций (room owner, event state, event close_at)
- ✅ Partial unique indexes (только одно OPEN событие, только один OWNER)
- ✅ Database constraints для целостности данных
- ⚠️ Polling mode (можно оптимизировать на long-polling или webhooks)

## Безопасность

- 🔒 Ролевая модель доступа (Owner → Admin → Member)
- 🔒 Проверка прав перед операциями (AccessControl service)
- 🔒 Уникальные инвайт-коды для присоединения к комнатам
- 🔒 Защита от частого создания событий (cooldown 5 минут)
- 🔒 Изоляция команд админа (is_admin flag)

## Проблемы и TODO

Смотрите [ARCHITECTURE.md](./docs/ARCHITECTURE.md) для подробного анализа архитектуры и слабых мест.

## Документация

- [README.md](README.md) - основная документация и quick start
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - детальный архитектурный анализ
- [DEVELOPMENT.md](DEVELOPMENT.md) - руководство по разработке
- [CONTRIBUTING.md](CONTRIBUTING.md) - гайд для контрибьюторов
- [CHANGELOG.md](CHANGELOG.md) - история изменений

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
