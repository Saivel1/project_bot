# Dockerfile
FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt ./

# Устанавливаем зависимости ГЛОБАЛЬНО (без venv в Docker)
RUN uv pip install --system -r requirements.txt

# Копируем код
COPY . .

# Создаем необходимые директории
RUN mkdir -p data logs

# Создаем пользователя
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck для бота
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import asyncio; import redis.asyncio as redis; asyncio.run(redis.from_url('redis://redis:6379').ping())" || exit 1

# Запуск через системный Python
CMD ["python", "main.py"]

