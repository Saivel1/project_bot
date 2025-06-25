import asyncio
from psycopg import AsyncConnection, Error
from db_conn import get_pg_connection
from typing import Any
import logging
logger = logging.getLogger(__name__)

async def main():
    connection: AsyncConnection | None = None

    try:
        connection = await get_pg_connection(
            db_name='bot_db',
            host='localhost',
            port=5432,
            user='iv',
            password='1234',
        )
        async with connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        query="""
                            SELECT version()
                        """
                    )
                    data = await cursor.fetchone()
                print(f"Tables `users` and `activity` were successfully created {data}")
    except Error as db_error:
        logger.exception("Database-specific error: %s", db_error)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
    finally:
        if connection:
            await connection.close()
            logger.info("Connection to Postgres closed")

asyncio.run(main())
