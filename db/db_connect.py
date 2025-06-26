import asyncio
import asyncpg
from typing import Any
import logging

logger = logging.getLogger(__name__)

async def get_pg_connection(
    db_name: str,
    host: str,
    port: int,
    user: str,
    password: str
) -> asyncpg.Connection:
    """Создает подключение к PostgreSQL через asyncpg"""
    return await asyncpg.connect(
        database=db_name,
        host=host,
        port=port,
        user=user,
        password=password
    )

async def main():
    connection: asyncpg.Connection | None = None

    try:
        connection = await get_pg_connection(
            db_name='telegram_bot_db',
            host='localhost',
            port=5433,
            user='bot_user',
            password='1234',
        )

        # asyncpg синтаксис немного отличается
        result = await connection.fetchrow("SELECT version()")
        print(f"PostgreSQL version: {result['version']}")

    except asyncpg.PostgresError as db_error:
        logger.exception("Database-specific error: %s", db_error)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.info("Connection to Postgres closed")

if __name__ == "__main__":
    asyncio.run(main())