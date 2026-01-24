# Development Setup Guide

## Prerequisites

- **Python 3.12+**
- **PostgreSQL 15+**
- **Docker & Docker Compose** (optional)
- **Git**

## Installation

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/bot_klima.git
cd bot_klima

# Copy environment template
cp env.example .env

# Edit .env with your values
# - Set real BOT_TOKEN from @BotFather
# - Configure database credentials

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/bot_klima.git
cd bot_klima

# Create virtual environment
python -m venv venv

# Activate (choose based on OS)
source venv/bin/activate       # macOS/Linux
# OR
venv\Scripts\activate          # Windows

# Install in development mode
pip install -e .

# Copy environment template
cp env.example .env

# Edit .env with your local database:
# DATABASE_URL=postgresql+asyncpg://klima:password@localhost:5432/klima
# BOT_TOKEN=your_real_token_from_botfather

# Start PostgreSQL (if not running)
# macOS: brew services start postgresql@15
# Linux: sudo systemctl start postgresql
# Windows: Use PostgreSQL installer or Docker

# Run migrations
alembic upgrade head

# Run bot (in terminal 1)
python -m app.bot

# Run worker (in terminal 2)
python -m app.worker
```

## Development Workflow

### Making Changes

1. Create feature branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

2. Install pre-commit hooks (optional)
```bash
pip install pre-commit
pre-commit install
```

3. Make changes and test locally

4. Run code quality checks
```bash
ruff check app/ --fix
ruff format app/
pyright app/
```

5. Run tests
```bash
pytest tests/ -v
```

6. Commit and push
```bash
git add .
git commit -m "feat: add amazing feature"
git push origin feature/my-feature
```

7. Open Pull Request on GitHub

### Database Changes

1. Make model changes in `app/repositories/db/models.py`

2. Create migration
```bash
alembic revision --autogenerate -m "Add new field"
```

3. Review generated migration in `alembic/versions/`

4. Apply migration
```bash
alembic upgrade head
```

5. Commit migration file
```bash
git add alembic/versions/*.py
git commit -m "migration: add new field"
```

### Testing

```bash
# All tests
pytest tests/

# Single test file
pytest tests/services/test_events.py

# Single test
pytest tests/services/test_events.py::test_create_event

# With coverage
pytest tests/ --cov=app --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

### Debugging

#### Print debugging
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Value: {value}")
```

#### Database debugging
```python
# Enable SQLAlchemy SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Telegram debugging
```python
# Set aiogram logging
import logging
logging.getLogger('aiogram').setLevel(logging.DEBUG)
```

#### Interactive debugging
```python
# Add breakpoint
breakpoint()  # Python 3.7+

# Or use pdb
import pdb; pdb.set_trace()
```

## Useful Commands

### Docker Compose

```bash
# Start services
docker-compose up

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Specific service
docker-compose logs -f bot

# Remove volumes (WARNING: deletes database)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Execute command in container
docker-compose exec bot bash
docker-compose exec db psql -U klima -d klima
```

### Database

```bash
# Connect to PostgreSQL
psql postgresql://klima:password@localhost:5432/klima

# List tables
\dt

# View migrations applied
SELECT * FROM alembic_version;

# Reset database (WARNING: deletes data)
dropdb klima
createdb klima
alembic upgrade head
```

### Code Quality

```bash
# Lint
ruff check app/

# Format
ruff format app/

# Type check
pyright app/

# All together
ruff check app/ && ruff format app/ && pyright app/
```

## Environment Variables

### Required

- `BOT_TOKEN` - Telegram bot token from @BotFather
- `DATABASE_URL` - PostgreSQL connection URL

### Optional

- `EVENT_CLOSER_INTERVAL_SECONDS` - Worker polling interval (default: 10)
- `LOG_LEVEL` - Logging level (default: DEBUG)

### Example .env

```env
# Telegram
BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh

# Database
POSTGRES_DB=klima
POSTGRES_USER=klima
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql+asyncpg://klima:your_secure_password_here@localhost:5432/klima

# Worker
EVENT_CLOSER_INTERVAL_SECONDS=10

# Logging
LOG_LEVEL=DEBUG
```

## Troubleshooting

### "Cannot connect to PostgreSQL"

```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check connection string in .env
# Format: postgresql+asyncpg://user:password@host:port/dbname

# Test connection manually
psql postgresql://klima:password@localhost:5432/klima
```

### "Bot token is invalid"

```bash
# Get new token from @BotFather
# 1. Open Telegram, find @BotFather
# 2. /start → /newbot → follow instructions
# 3. Copy token to BOT_TOKEN in .env
```

### "Migrations pending"

```bash
alembic upgrade head
```

### "Tests failing"

```bash
# Check PostgreSQL is running
docker-compose ps db

# Check DATABASE_URL in .env (should use _test database for tests)
# Run migrations for test DB
export DATABASE_URL=postgresql+asyncpg://klima:password@localhost:5432/klima_test
alembic upgrade head

# Run tests
pytest tests/ -v
```

### "Permission denied" on Unix

```bash
# Fix file permissions
chmod +x venv/bin/activate
```

## IDE Setup

### VS Code

1. Install Python extension
2. Select interpreter: `venv/bin/python`
3. Install Ruff extension (id: charliermarsh.ruff)
4. Install Pylance extension (id: ms-python.vscode-pylance)

### PyCharm

1. Configure Python interpreter: `venv/bin/python`
2. Mark `app/` as Source Root
3. Configure run configuration for `app/bot.py`
4. Enable ruff as code style tool

## Resources

- [aiogram Documentation](https://docs.aiogram.dev/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

## Getting Help

- 📖 Read [README.md](../README.md)
- 📐 Check [docs/ARCHITECTURE.md](./ARCHITECTURE.md)
- 🐛 Open [GitHub issue](https://github.com/yourusername/bot_klima/issues)
- 💬 Start [GitHub discussion](https://github.com/yourusername/bot_klima/discussions)

---

Happy coding! 🚀
