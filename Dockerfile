FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml

# Simple deps install without lockfile. In production you may pin via uv/poetry/pip-tools.
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir .

COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

CMD sh -c "alembic upgrade head && python -m app.bot"

