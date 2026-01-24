# Рекомендации для контрибьютеров

Спасибо за интерес к проекту! Это руководство поможет вам начать.

## Процесс разработки

### 1. Setup

```bash
git clone https://github.com/yourusername/bot_klima.git
cd bot_klima
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 2. Branches

- `main` - production-ready код
- `develop` - интеграционная ветка
- `feature/*` - новые функции
- `fix/*` - исправления багов
- `docs/*` - документация

Создавайте branch от `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### 3. Code Style

Проект использует:
- **Formatter:** Ruff
- **Linter:** Ruff
- **Type checker:** Pyright

Перед коммитом:
```bash
ruff format app/
ruff check app/ --fix
pyright app/
```

### 4. Commits

Следуйте conventional commits:
```
feat: add new feature
fix: resolve bug in module
docs: update README
refactor: improve code quality
test: add unit tests
chore: update dependencies
```

Хорошие коммиты:
- ✅ Atomic (одна логическая единица)
- ✅ Descriptive (понятное описание)
- ✅ Tested (код протестирован)

### 5. Pull Requests

- Описание что изменилось и почему
- Reference related issues (`Fixes #123`)
- Screenshots если UI изменилась
- Минимум одобрение перед merge

Шаблон PR:
```markdown
## Description
Что это изменяет?

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
Как это протестировали?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Архитектурные рекомендации

### Layers

**Handlers** → **Services** → **Repositories** → **Database**

- ❌ Handlers не должны напрямую работать с БД
- ❌ Services не должны содержать Telegram-специфичный код
- ✅ Repositories только для data access
- ✅ Services содержат бизнес-логику

### Async/Await

Все должно быть асинхронным:
```python
# ✅ Good
async def create_event(self, room_id: UUID) -> None:
    await self._service.create_event(room_id)

# ❌ Bad
def create_event(self, room_id: UUID) -> None:
    asyncio.run(self._service.create_event(room_id))
```

### Database State

Источник истины - **база данных**, не FSM:
```python
# ✅ Good
room = await rooms_repo.get(room_id)
if room.state == RoomState.ACTIVE:
    # proceed

# ❌ Bad  
if user_state.get("room_id") == room_id:
    # proceed (FSM могут потеряться!)
```

### Error Handling

Используйте custom exceptions:
```python
# app/domain/exceptions.py
class ConflictError(Exception):
    """Когда состояние конфликтует с операцией"""
    pass

class AccessDeniedError(Exception):
    """Когда user не имеет прав"""
    pass
```

```python
# В handlers
try:
    await service.delete_room(room_id, user_id)
except AccessDeniedError:
    await message.answer("❌ Только владелец может удалить комнату")
except ConflictError as e:
    await message.answer(f"❌ {e}")
```

## Testing

### Unit Tests

```python
# tests/services/test_event_service.py
import pytest
from app.services.events import EventService

@pytest.mark.asyncio
async def test_create_event_requires_active_room(uow_factory):
    uow = await uow_factory()
    service = EventService(...)
    
    with pytest.raises(ConflictError):
        await service.create_event(
            room_id=archived_room_id,
            creator_id=user_id,
            event_type=EventType.SMOKE,
            auto_close_minutes=5,
        )
```

### Integration Tests

```python
# tests/integration/test_event_flow.py
@pytest.mark.asyncio
async def test_event_creation_flow(telegram_bot, db_session):
    # Setup
    room_id = await create_test_room()
    
    # Act
    await telegram_bot.send_message(
        chat_id=user_id,
        text="/create_event smoke 5"
    )
    
    # Assert
    event = await db_session.get_latest_event()
    assert event.state == EventState.OPEN
    assert event.close_at is not None
```

### Database Fixtures

```python
# conftest.py
@pytest.fixture
async def db_session():
    async with test_sessionmaker() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_room(db_session):
    room = await RoomRepository(db_session).create(
        name="Test Room",
        owner_id=123456
    )
    return room
```

## Documentation

- Добавляйте docstrings для всех public методов
- Обновляйте README если меняется API
- Документируйте миграции в `alembic/versions/`

### Docstring Example

```python
async def create_event(
    self,
    *,
    room_id: UUID,
    creator_id: int,
    event_type: EventType,
    auto_close_minutes: int | None,
) -> UUID:
    """
    Create a new open event in a room.
    
    Only room members can create events. The creator is automatically
    marked as ACCEPTED. Participation records are created for all
    active members.
    
    Args:
        room_id: Target room UUID
        creator_id: Telegram user ID of event creator
        event_type: Type of event (SMOKE, COFFEE, WALK, CUSTOM)
        auto_close_minutes: Auto-close timeout in minutes (optional)
    
    Returns:
        UUID of created event
        
    Raises:
        AccessDeniedError: If user is not a room member
        ConflictError: If room is not ACTIVE or event already OPEN
    """
    ...
```

## Performance Tips

- Используйте批量操作вместо циклов
- Добавляйте индексы на часто запрашиваемые поля
- Профилируйте с `asyncpg --debug`
- Проверяйте query count в тестах

## Security

- ❌ Никогда не коммитьте `.env` с реальными токенами
- ❌ Не логируйте чувствительные данные (BOT_TOKEN, passwords)
- ✅ Всегда валидируйте user input
- ✅ Проверяйте права доступа перед любой операцией
- ✅ Используйте параметризованные запросы (SQLAlchemy это делает)

## Getting Help

- 📖 Смотрите [README.md](README.md)
- 📐 Смотрите [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 💬 Откройте discussion в GitHub
- 🐛 Если нашли баг - откройте issue

---

**Спасибо за контрибуцию! 🎉**
