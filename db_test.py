#!/usr/bin/env python3
"""
Простой скрипт для тестирования подключения к PostgreSQL через asyncpg
"""
import asyncio
import asyncpg
import sys

async def test_connection():
    """Тестирует подключение к PostgreSQL"""

    # Параметры подключения - измените на свои
    connection_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'bot_user',  # или имя вашей БД
        'user': 'bot_user',
        'password': '1234'  # укажите пароль если есть
    }

    try:
        print("Попытка подключения к PostgreSQL...")
        print(f"Host: {connection_params['host']}")
        print(f"Port: {connection_params['port']}")
        print(f"Database: {connection_params['database']}")
        print(f"User: {connection_params['user']}")
        print("-" * 40)

        # Подключаемся к базе данных
        conn = await asyncpg.connect(**connection_params)

        # Выполняем простой запрос
        version = await conn.fetchval('SELECT version()')
        user_info = await conn.fetchrow('SELECT current_user, current_database()')

        print("✅ Подключение успешно!")
        print(f"Версия PostgreSQL: {version}")
        print(f"Текущий пользователь: {user_info['current_user']}")
        print(f"Текущая база данных: {user_info['current_database']}")

        # Закрываем соединение
        await conn.close()
        return True

    except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
        print("❌ Ошибка аутентификации!")
        print("Проверьте имя пользователя и пароль")

    except asyncpg.exceptions.InvalidCatalogNameError:
        print("❌ База данных не найдена!")
        print(f"База данных '{connection_params['database']}' не существует")

    except asyncpg.exceptions.ConnectionDoesNotExistError:
        print("❌ Не удается подключиться к серверу!")
        print("Проверьте, что PostgreSQL запущен")

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print(f"Тип ошибки: {type(e).__name__}")

    return False

async def main():
    print("=== Тест подключения к PostgreSQL через asyncpg ===\n")

    success = await test_connection()

    if not success:
        print("\n=== Возможные решения ===")
        print("1. Убедитесь, что PostgreSQL запущен:")
        print("   sudo systemctl status postgresql")
        print("   sudo systemctl start postgresql")

        print("\n2. Проверьте пароль пользователя postgres:")
        print("   sudo -u postgres psql")
        print("   \\password postgres")

        print("\n3. Проверьте настройки в pg_hba.conf:")
        print("   sudo nano /etc/postgresql/*/main/pg_hba.conf")
        print("   Найдите строку: local all postgres peer")
        print("   Измените на: local all postgres trust")

        print("\n4. Перезапустите PostgreSQL:")
        print("   sudo systemctl restart postgresql")

if __name__ == "__main__":
    # Проверяем наличие asyncpg
    try:
        import asyncpg
    except ImportError:
        print("❌ Модуль asyncpg не установлен!")
        print("Установите его командой: pip install asyncpg")
        sys.exit(1)

    # Запускаем тест
    asyncio.run(main())