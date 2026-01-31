# Архитектурный анализ проекта "Возьмите Клима"

## Содержание

1. [Общая архитектура](#общая-архитектура)
2. [Точки входа](#точки-входа)
3. [Зависимости и связи](#зависимости-и-связи)
4. [Компоненты](#компоненты)
5. [Паттерны](#ключевые-паттерны)
6. [Слабые места](#слабые-места)
7. [Рекомендации](#рекомендации)

---

## Общая архитектура

Проект построен по **многоуровневой архитектуре (Layered Architecture)** с четким разделением ответственности:

```
┌─────────────────────────────────┐
│   Telegram UI Layer (aiogram)    │
│ (handlers: commands, callbacks)  │
├─────────────────────────────────┤
│   Application Layer (services)   │
│ (business logic & orchestration) │
├─────────────────────────────────┤
│   Domain Layer (enums, errors)   │
│ (business rules & invariants)    │
├─────────────────────────────────┤
│   Data Access Layer (repos)      │
│  (UOW pattern, repositories)     │
├─────────────────────────────────┤
│   Database Layer (SQLAlchemy)    │
│  (async engine, session mgmt)    │
└─────────────────────────────────┘
```

### Ключевые характеристики

✅ **Async-only** - вся архитектура построена на asyncio (нет блокирующих операций)
✅ **Clean separation** - UI полностью отделена от бизнес-логики
✅ **Database as source of truth** - состояние хранится в БД, не в FSM
✅ **No global state** - максимум локального и контролируемого контекста
✅ **Event-driven** - все реактивно на события от Telegram

---

## Точки входа

### 1. **Main Bot Process** (`app/bot.py`)

```python
async def main() -> None:
    settings = load_settings()          # Загрузить конфиг из .env
    container = build_container(settings)  # DI
    bot = Bot(token=settings.bot_token) # Telegram Bot API client
    
    dp = Dispatcher()
    dp.update.middleware(UnitOfWorkMiddleware(...))  # Inject UoW
    dp.include_router(...)              # Регистрация handlers
    
    await dp.start_polling(bot)         # Polling loop
```

**Запуск:** `python -m app.bot` или `docker-compose up bot`

**Отвечает за:**
- Инициализация Telegram bot'а
- Установка middleware'ов
- Регистрация всех обработчиков
- Polling loop для получения обновлений

### 2. **Background Worker** (`app/worker.py`)

```python
async def main() -> None:
    settings = load_settings()
    container = build_container(settings)
    uow = UnitOfWork(container.sessionmaker)
    
    while True:  # Periodic polling
        async with uow:
            expired = await events.list_expired_open_events()
            for event_id in expired:
                await events.close_event(event_id)
        await asyncio.sleep(settings.event_closer_interval_seconds)
```

**Запуск:** `python -m app.worker` или `docker-compose up worker`

**Отвечает за:**
- Автоматическое закрытие истекших событий
- Периодическое сканирование БД (polling)
- Изолированная транзакция для каждого цикла

### 3. **Docker Compose Orchestration** (`docker-compose.yml`)

```yaml
services:
  db:           # PostgreSQL 16
  bot:          # Main polling process
  worker:       # Background event closer
```

---

## Зависимости и связи

### Внешние зависимости

```
aiogram 3.x          → Telegram Bot API (polling)
SQLAlchemy 2.0       → ORM async + session management
asyncpg              → PostgreSQL driver (async)
pydantic 2.x         → Settings validation
alembic              → Database migrations
psycopg2-binary      → PostgreSQL driver (fallback)
```

### Внутренние потоки данных

**Поток 1: Telegram Update → Handler → Service → Repository → DB**

```
Message/Callback from Telegram
         ↓
Handler (async def in commands/callbacks)
         ↓
UnitOfWorkMiddleware creates fresh UoW
         ↓
Service layer (EventService, RoomService, etc.)
         ↓
Business logic validation & orchestration
         ↓
Repository layer (EventRepository, RoomRepository, etc.)
         ↓
SQLAlchemy ORM Operations
         ↓
Database (PostgreSQL)
         ↓
[UoW context exit]
         ↓
Auto-commit (if no exception) or rollback
         ↓
Response sent to Telegram API
```

**Поток 2: Worker → Repository → Database**

```
Worker polling loop
         ↓
Query: SELECT * FROM events WHERE state=OPEN AND close_at < NOW()
         ↓
For each expired event:
  - Update state to CLOSED
  - Commit transaction
         ↓
Sleep for N seconds
         ↓
Repeat
```

### Зависимости между слоями

```
handlers/
  ├─ depends on → services/
  ├─ depends on → repositories/
  └─ depends on → domain/

services/
  ├─ depends on → repositories/
  ├─ depends on → domain/
  └─ depends on → exceptions/

repositories/
  ├─ depends on → domain/
  └─ depends on → db/models

db/
  └─ models only depend on SQLAlchemy & enums
```

---

## Компоненты

### 1. Domain Layer (`app/domain/`)

**Содержит:**
- Перечисления состояний (`enums/`)
- Исключения (`exceptions/`)
- Бизнес-правила и инварианты

**Файлы:**
- `enums/user.py` - `UserGlobalStatus` (ACTIVE, VACATION, DISABLED)
- `enums/room.py` - `RoomState` (CREATED, ACTIVE, ARCHIVED), `RoomRole` (OWNER, ADMIN, MEMBER)
- `enums/event.py` - `EventState` (CREATED, OPEN, CLOSED), `EventType` (SMOKE, COFFEE, WALK, CUSTOM), `ParticipationState`
- `exceptions/__init__.py` - `ConflictError`, `AccessDeniedError`

**Принцип:** Domain layer НЕ зависит ни от чего другого (кроме Python standard lib)

### 2. Repositories Layer (`app/repositories/`)

**Паттерны:**
- Repository pattern для data access
- Unit of Work для управления транзакциями
- Session per request (via middleware)

**Компоненты:**
- `UnitOfWork` - контекст-менеджер для транзакций
- `EventRepository` - CRUD события
- `ParticipationRepository` - управление участием в событиях
- `RoomRepository` - CRUD комнаты
- `RoomMemberRepository` - управление членством в комнатах
- `UserRepository` - профили пользователей

**Пример использования:**
```python
async with uow:
    events = EventRepository(uow.session)
    event = await events.require(event_id)
    # Changes auto-flush to DB
# On __aexit__: auto-commit or rollback
```

### 3. Services Layer (`app/services/`)

**Содержит бизнес-логику:**
- `EventService` - создание событий, управление участниками, закрытие событий
- `RoomService` - создание/удаление комнат, управление членством, инвайт-коды
- `UserService` - управление профилями, статусом отпуска
- `AccessControl` - ролевые проверки и авторизация
- `NotificationService` - отправка Telegram обновлений
- `AdminService` - административные функции (выдача/отзыв прав админа)

**Характеристики:**
- НЕ содержат Telegram-специфичный код
- Оркестрируют работу repositories
- Проверяют инварианты и бизнес-правила
- Транзакционны (работают с UoW)
- Реализуют защиту от спама (cooldown на создание событий)

**Пример:**
```python
async def create_event(
    self,
    *,
    room_id: UUID,
    creator_id: int,
    event_type: EventType,
) -> UUID:
    # 1. Check access
    await self._access.require_role_at_least(room_id, creator_id, ...)
    
    # 2. Validate state
    room = await self._rooms.require(room_id)
    if room.state != RoomState.ACTIVE:
        raise ConflictError("only ACTIVE rooms")
    
    # 3. Create event
    event = await self._events.create_open_event(...)
    
    # 4. Create participations for all members
    member_ids = await self._room_members.list_member_ids(room_id)
    for uid in member_ids:
        await self._participations.create(event_id, uid, ...)
    
    return event.id
```

### 4. Handlers Layer (`app/handlers/`)

**Структура:**
```
handlers/
├── commands/          # /start, /rooms, /events, /status
├── callbacks/         # Button click handlers
├── middlewares/       # UoW injection, filters
└── ui/               # Keyboards, message templates
```

**Командные handlers:**
- `/start` - инициализация user'а, отображение главного меню
- `/rooms` - список комнат с inline buttons
- `/create_room <name>` - создание новой комнаты
- `/join_room <invite_code>` - присоединение по инвайт-коду
- `/delete_room <room_id>` - удаление комнаты (только owner)
- `/events` - список событий в выбранной комнате
- `/create_event <type> [minutes]` - создание события
- `/status_on` - включить vacation mode
- `/status_off` - выключить vacation mode
- `/admin_grant <user_id>` - выдать админ-права (только для админов)
- `/admin_revoke <user_id>` - забрать админ-права (только для админов)

**Callback handlers:**
- Обработка нажатий на inline buttons
- Управление участием в событиях (accept/decline/later)
- Навигация по меню и комнатам
- Обновление списков (refresh on button press)

**Middleware:**
- `UnitOfWorkMiddleware` - создает UoW и инъектирует в data
- `AdminMiddleware` - проверка прав админа для admin-команд

### 5. Database Layer (`app/repositories/db/`)

**SQLAlchemy models:**

```python
# UserModel
id: BigInteger (Telegram ID, PK)
username: str | null
display_name: str
global_status: Enum(UserGlobalStatus)
vacation_until: DateTime (nullable)
is_admin: bool (default: false)
last_menu_message_id: BigInteger (nullable)
last_invite_message_id: BigInteger (nullable)

# RoomModel
id: UUID (PK)
name: str
invite_code: str (unique, nullable)
open_event_id: UUID (FK Event, nullable)
owner_id: BigInteger (FK User)
state: Enum(RoomState)

# RoomMemberModel
room_id: UUID (FK, PK)
user_id: BigInteger (FK, PK)
role: Enum(RoomRole)
# Constraint: один OWNER на комнату (partial unique index)

# EventModel
id: UUID (PK)
room_id: UUID (FK)
creator_id: BigInteger (FK User)
type: Enum(EventType)  # SMOKE | COFFEE | WALK | CUSTOM
state: Enum(EventState)  # CREATED | OPEN | CLOSED
custom_description: str (nullable)
created_at: DateTime
close_at: DateTime (nullable)
creator_message_id: BigInteger (nullable)
# Constraint: одно OPEN событие на комнату (partial unique index)

# ParticipationModel
event_id: UUID (FK, PK)
user_id: BigInteger (FK, PK)
state: Enum(ParticipationState)  # ACCEPTED | DECLINED | LATER | VACATION
note: text (nullable)
```

**Session management:**
```python
# Async engine with connection pooling
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=10,
)

# Session factory (used by UoW)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
```

---

## Ключевые паттерны

### 1. Unit of Work Pattern

**Назначение:** Явное управление транзакциями, isolate database operations

```python
async with UnitOfWork(sessionmaker) as uow:
    events = EventRepository(uow.session)
    room = await events.require(room_id)
    room.state = RoomState.ACTIVE
    # Changes tracked
# On exit: auto-commit if no exception, rollback on exception
```

**Преимущества:**
- ✅ Четкие границы транзакции
- ✅ Atomicity гарантирована
- ✅ Нет global state
- ✅ Легко тестировать (можно мокировать session)

### 2. Middleware Injection

**UnitOfWorkMiddleware:** Создает fresh UoW для каждого Telegram update

```python
class UnitOfWorkMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        data["uow"] = UnitOfWork(self._sessionmaker)
        return await handler(event, data)

# В handler:
async def some_handler(message: Message, uow: UnitOfWork):
    async with uow:
        # use uow.session
```

**Преимущества:**
- ✅ Изоляция между запросами
- ✅ Автоматический cleanup
- ✅ Нет утечек соединений
- ✅ Детерминированное поведение

### 3. Repository Pattern

**Абстрактный слой для data access**

```python
class EventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create_open_event(self, ...) -> EventModel:
        event = EventModel(...)
        self._session.add(event)
        await self._session.flush()  # Get ID from DB
        return event
    
    async def list_expired_open_events(self) -> list[UUID]:
        stmt = select(EventModel.id).where(
            (EventModel.state == EventState.OPEN) &
            (EventModel.close_at < func.now())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
```

**Преимущества:**
- ✅ Изоляция database details
- ✅ Легко свопить реализацию (in-memory для тестов)
- ✅ Single responsibility
- ✅ Type-safe (с async)

### 4. Service Orchestration

**Services как бизнес-логика слой**

```python
class EventService:
    def __init__(self, events, rooms, members, users, access):
        self._events = events      # repositories
        self._rooms = rooms
        self._members = members
        self._users = users
        self._access = access      # domain service
    
    async def create_event(self, room_id, creator_id, event_type):
        # 1. Authorization
        await self._access.require_role_at_least(...)
        
        # 2. Validation
        room = await self._rooms.require(room_id)
        if room.state != RoomState.ACTIVE:
            raise ConflictError(...)
        
        # 3. Business logic
        event = await self._events.create_open_event(...)
        member_ids = await self._members.list_member_ids(room_id)
        
        # 4. Data updates
        for uid in member_ids:
            await self._participations.create(...)
        
        return event.id
```

**Преимущества:**
- ✅ Бизнес-правила в одном месте
- ✅ Переиспользуемость (один service для разных handlers)
- ✅ Простота тестирования (можно мокировать repos)
- ✅ Нет Telegram-специфичного кода

### 5. Dependency Injection

**Простой DI контейнер**

```python
@dataclass(frozen=True)
class Container:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]

def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.database_url)
    sessionmaker = create_sessionmaker(engine)
    return Container(settings, engine, sessionmaker)

# Использование в bot.py:
container = build_container(settings)
dp.update.middleware(UnitOfWorkMiddleware(container.sessionmaker))
```

---

## Слабые места

### 🔴 Критические проблемы

#### 1. Отсутствие global exception handler

**Проблема:** Если в handler выбросится исключение, оно не будет обработано
```python
# handlers/commands/events.py
async def create_event_cmd(message, uow):
    await service.create_event(...)  # ← Может выбросить исключение
    await message.answer("Event created")  # ← Не выполнится если exception
```

**Последствия:**
- ❌ User не получит feedback
- ❌ Bot может зависнуть или crash'иться
- ❌ Exception попадает в logs без graceful handling

**Решение:**
```python
# bot.py
async def handle_exception(update: Update, exception: Exception):
    logger.error(f"Unhandled exception: {exception}", exc_info=exception)
    if isinstance(exception, ConflictError):
        await message.answer(f"❌ {exception}")
    elif isinstance(exception, AccessDeniedError):
        await message.answer("❌ You don't have permission")
    else:
        await message.answer("❌ Internal error. Please try again later")

dp.error.register(handle_exception)
```

#### 2. Race condition при создании participations

**Проблема:** EventService создает participations в цикле вне БД
```python
# services/events.py
async def create_event(self, ...):
    event = await self._events.create_open_event(...)  # ← INSERT event
    member_ids = await self._room_members.list_member_ids(room_id)
    
    for uid in member_ids:  # ← Цикл в Python
        await self._participations.create(event_id, uid, ...)  # ← N INSERT'ов
        # ↑ Если упадем здесь, participations будут неполные!
```

**Последствия:**
- ❌ Если процесс упадет, participations могут быть неполные
- ❌ Event существует, но не все члены знают о нем
- ❌ Сложно debug'ить

**Решение:**
```python
# Batch insert одной операцией
async def bulk_create_participations(
    self, event_id: UUID, user_ids: list[int]
) -> None:
    stmt = insert(ParticipationModel).values([
        {"event_id": event_id, "user_id": uid, "state": ParticipationState.PENDING}
        for uid in user_ids
    ])
    await self._session.execute(stmt)
```

#### 3. Отсутствие idempotency protection

**Проблема:** Если Telegram retry'т callback дважды, создастся 2 события
```
User clicks button
Bot processes, sends response
Response gets lost
Telegram retry's callback (duplicate)
Bot creates duplicate event
```

**Решение:** Idempotency keys
```python
# models.py
class EventModel:
    id: UUID
    idempotency_key: str | None  # Уникальный ключ
    # ...

# handlers/callbacks/events.py
async def create_event_cb(cb, callback_data, uow):
    idempotency_key = f"{cb.from_user.id}:{cb.id}:{time.time()}"
    try:
        event = await service.create_event(
            room_id=...,
            idempotency_key=idempotency_key,
        )
        await cb.answer("✅ Event created")
    except DuplicateKeyError:
        await cb.answer("✅ Event created (cached)")
```

### 🟡 Средние проблемы

#### 1. Недостаточное логирование

**Проблема:** Только базовый logging, нет структурированного
```python
# bot.py
logging.basicConfig(level=logging.DEBUG, format='...')
```

**Последствия:**
- 🟡 Сложно отследить user flow в production
- 🟡 Нельзя быстро найти ошибку в логах

**Решение:** Structured logging
```python
import structlog

logger = structlog.get_logger()

# В handlers:
logger.info(
    "event_created",
    event_id=str(event.id),
    user_id=creator_id,
    room_id=str(room_id),
    elapsed_ms=time.time() - start_time,
)
```

#### 2. Отсутствие rate limiting

**Проблема:** Ничего не защищает от spam/abuse
```
User clicks "create event" 100 times in 1 second
Bot creates 100 events
```

**Решение:** Rate limiting middleware
```python
from aiogram import types
from aiogram.filters import Command

class RateLimitFilter:
    def __init__(self, calls: int, period: int):
        self.calls = calls      # calls
        self.period = period    # seconds
        self.buckets = {}       # user_id -> list[timestamp]
    
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        now = time.time()
        
        if user_id not in self.buckets:
            self.buckets[user_id] = []
        
        # Удалить старые events
        self.buckets[user_id] = [
            ts for ts in self.buckets[user_id]
            if now - ts < self.period
        ]
        
        if len(self.buckets[user_id]) >= self.calls:
            return False  # Reject
        
        self.buckets[user_id].append(now)
        return True

# Использование:
rate_limit = RateLimitFilter(calls=5, period=60)  # 5 calls per 60 sec
dp.include_router(events_router, filters=[rate_limit])
```

#### 3. N+1 queries в EventService.create_event

**Проблема:**
```python
member_ids = await self._room_members.list_member_ids(room_id)  # 1 query
for uid in member_ids:
    u = await self._users.get(uid)  # N queries (one per user!)
    if u.global_status == UserGlobalStatus.DISABLED:
        continue
```

**Решение:** Batch fetch
```python
# services/events.py
async def create_event(self, ...):
    # ...
    member_ids = await self._room_members.list_member_ids(room_id)
    
    # Fetch all users at once
    users_map = await self._users.get_many(member_ids)
    
    active_ids = [
        uid for uid, user in users_map.items()
        if user.global_status != UserGlobalStatus.DISABLED
    ]
    
    await self._participations.bulk_create(event_id, active_ids)
```

#### 4. FSM и Database state mismatch

**Проблема:** Используются и FSM и Database для состояния
```python
# handlers/callbacks/menu.py
state = FSMContext()
await state.set_state(MenuStates.WaitingForRoomName)

# Но также есть room.state в БД
room.state = RoomState.ACTIVE
```

**Следствие:**
- 🟡 Противоречие (какой source of truth?)
- 🟡 Если бот crash'ится, FSM теряется
- 🟡 Сложнее разобраться в логике

**Решение:** Документировать правило
```
FSM = только для UX flow (временные шаги в диалоге)
Database state = бизнес-состояние (постоянное)

Пример:
FSM.WaitingForRoomName    → user вводит название комнаты
  ↓
room.state = CREATED      → сохранено в БД
```

### 🟠 Архитектурные проблемы

#### 1. Отсутствие API contract schema

**Проблема:** Нет документации what callbacks expect
```python
# handlers/callbacks/rooms.py
async def room_create_event_from_button(
    cb: CallbackQuery,
    callback_data: RoomDeleteCb,  # ← Какой формат?
    ...
):
```

**Решение:** Pydantic schemas
```python
# handlers/callbacks/schemas.py
from pydantic import BaseModel

class RoomDeleteCb(BaseModel):
    room_id: str  # UUID as string
    user_id: int

# handlers/callbacks/rooms.py
async def room_create_event_from_button(
    cb: CallbackQuery,
    callback_data: RoomDeleteCb,
    uow: UnitOfWork,
):
    # callback_data is validated at dispatch time
    ...
```

#### 2. Отсутствие monitoring/observability

**Проблема:** Нет видимости в production
- 🔴 Нет metrics (requests/sec, errors/sec)
- 🔴 Нет tracing (какой handler сколько времени?)
- 🔴 Нет алертов (error rate spike)

**Решение:** Добавить Prometheus + OpenTelemetry
```python
from prometheus_client import Counter, Histogram

event_creates = Counter("event_creates_total", "Total events created")
event_create_duration = Histogram("event_create_duration_seconds")

@event_create_duration.time()
async def create_event_cmd(message: Message, uow: UnitOfWork):
    try:
        await service.create_event(...)
        event_creates.inc()
    except Exception as e:
        errors.labels(handler="create_event").inc()
        raise
```

#### 3. Database migrations не автоматизированы

**Проблема:** Alembic есть, но не запускается при старте
```dockerfile
# Dockerfile
CMD sh -c "alembic upgrade head && python -m app.bot"
```

Это нестабильно в production (race condition если несколько реплик)

**Решение:** Отдельный init job
```yaml
# docker-compose.yml
services:
  db-migrate:
    build: .
    command: ["alembic", "upgrade", "head"]
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: ...
  
  bot:
    depends_on:
      db-migrate:
        condition: service_completed_successfully  # Wait for migrations
```

---

## Рекомендации

### Текущее состояние (Январь 2026)

Проект находится в **стадии активной разработки**:
- ✅ Основная функциональность реализована
- ✅ Система инвайт-кодов для комнат
- ✅ Поддержка кастомных событий
- ✅ Админ-панель
- ✅ Умная очистка служебных сообщений
- ✅ 8 миграций базы данных применены
- ⚠️ Отсутствуют тесты
- ⚠️ Минимальный error handling
- ⚠️ Нет мониторинга

### Short term (1-2 недели)

**Критичные улучшения:**
1. ✅ Добавить global exception handler в Dispatcher
2. ✅ Batch create participations (исправить race condition)
3. ✅ Добавить structured logging (structlog)
4. 🔴 Написать unit tests для сервисов (pytest)
5. 🔴 Добавить integration tests для handlers
6. ✅ Документировать callback schemas

**Code quality:**
- Включить pre-commit hooks (ruff, pyright)
- Добавить coverage tracking (минимум 70%)
- Написать docstrings для публичных методов

### Medium term (1-2 месяца)

**Надежность:**
1. 📝 Реализовать idempotency protection для событий
2. 🔒 Добавить rate limiting на команды
3. 📊 Prometheus metrics для основных операций
4. 📋 Request ID tracking для debugging
5. 🗄️ Optimize N+1 queries (batch fetching)

**Функциональность:**
- Уведомления о начале/закрытии событий
- Экспорт статистики событий
- Архивирование старых комнат
- Поддержка временных зон

### Long term (3+ месяца)

**Production-ready:**
1. 🎯 Migration на webhook mode (вместо polling)
2. 📈 OpenTelemetry distributed tracing
3. 🧪 E2E tests с реальным Telegram API
4. 📦 Redis кэширование для user profiles
5. 🚀 Database query optimization (materialized views)

**Масштабирование:**
- Horizontal scaling (multiple bot replicas)
- Background job queue (Celery/RQ)
- CDN для медиа-файлов
- Sharding базы данных

---

## Приложения

### Список основных файлов

**Конфигурация:**
- `pyproject.toml` - зависимости, метаданные
- `alembic.ini` - настройки миграций
- `docker-compose.yml` - оркестрация контейнеров
- `Dockerfile` - образ приложения
- `.env` - переменные окружения (не в git)

**Точки входа:**
- `app/bot.py` - main polling process
- `app/worker.py` - background event closer
- `app/config.py` - settings validation
- `app/di.py` - dependency injection container

**Бизнес-логика:**
- `app/services/events.py` - управление событиями
- `app/services/rooms.py` - управление комнатами
- `app/services/users.py` - управление пользователями
- `app/services/access.py` - контроль доступа
- `app/services/admin.py` - административные функции
- `app/services/notifications.py` - Telegram уведомления

**Данные:**
- `app/repositories/db/models.py` - ORM модели
- `app/repositories/events.py` - data access для событий
- `app/repositories/rooms.py` - data access для комнат
- `app/repositories/users.py` - data access для пользователей
- `app/repositories/uow.py` - Unit of Work pattern

**Telegram UI:**
- `app/handlers/commands/*.py` - command handlers
- `app/handlers/callbacks/*.py` - callback handlers
- `app/ui/keyboards.py` - inline клавиатуры
- `app/ui/messages.py` - шаблоны сообщений

### Миграции базы данных (в порядке применения)

1. `0001_initial.py` - создание базовых таблиц
2. `0002_add_creator_message_id.py` - ID сообщения создателя события
3. `0003_add_invite_code.py` - система инвайт-кодов
4. `0004_add_open_event_id.py` - связь комнаты с открытым событием
5. `0005_restore_owner_roles.py` - исправление ролей владельцев
6. `0006_add_user_last_messages.py` - хранение ID последних сообщений
7. `0007_add_user_is_admin.py` - флаг администратора
8. `0008_add_custom_event_type.py` - поддержка кастомных событий

---

## Качество кода

| Метрика | Оценка | Комментарий |
|---------|--------|-----------|
| **Cohesion** | ✅ Хорошо | Каждый слой четко разделен |
| **Coupling** | 🟡 Среднее | UI знает про services (ok) |
| **Testability** | 🟡 Среднее | Можно улучшить (нет абстракций repo) |
| **Maintainability** | 🟡 Среднее | Хорошая структура, нужна документация |
| **Security** | 🟡 Среднее | Базовое, нужны rate limits + input validation |
| **Scalability** | 🔴 Ограниченная | Polling вместо events; single worker |
| **Observability** | 🔴 Плохо | Нет metrics, трассировки, алертов |

---

**Вывод:** Проект имеет хороший архитектурный фундамент, но нуждается в production-ready практиках для deployment в production.
