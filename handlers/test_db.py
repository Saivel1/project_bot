from datetime import datetime
from dataclasses import dataclass
import asyncio
import asyncpg
from typing import Any, Optional, List
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass(slots=True, frozen=True)
class UserActions:
    callback: str = ''
    message: str = ''
    user_id: int = 0
    timestamp: int = 0
    action_id: int = 0

class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, db_name: str, host: str, port: int, user: str, password: str):
        self.db_name = db_name
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    async def __aenter__(self):
        self.connection = await self.get_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'connection') and self.connection:
            await self.connection.close()

    async def get_connection(self) -> asyncpg.Connection:
        """Создает подключение к PostgreSQL"""
        try:
            return await asyncpg.connect(
                database=self.db_name,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    async def create_table(self) -> bool:
        """Создает таблицу user_actions"""
        connection = None
        try:
            connection = await self.get_connection()

            await connection.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    action_id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    callback VARCHAR(255) DEFAULT '',
                    message TEXT DEFAULT '',
                    timestamp BIGINT NOT NULL
                );
            ''')
            return True

        except Exception as e:
            logger.error(f"Ошибка создания таблицы: {e}")
            return False
        finally:
            if connection:
                await connection.close()

    async def insert_action(self, data: UserActions) -> bool:
        """Вставляет данные в таблицу user_actions"""
        connection = None
        try:
            connection = await self.get_connection()

            result = await connection.execute('''
                INSERT INTO user_actions (user_id, callback, message, timestamp)
                VALUES ($1, $2, $3, $4)
            ''', data.user_id, data.callback, data.message, data.timestamp)
            return True

        except Exception as e:
            logger.error(f"Ошибка вставки данных: {e}")
            return False
        finally:
            if connection:
                await connection.close()

    async def get_all_actions(self) -> List[UserActions]:
        """Получает все записи из таблицы user_actions"""
        connection = None
        try:
            connection = await self.get_connection()

            # Используем fetch вместо fetchval для получения всех записей
            rows = await connection.fetch('''
                SELECT action_id, user_id, callback, message, timestamp
                FROM user_actions
                ORDER BY action_id DESC;
            ''')

            # Преобразуем результат в список объектов UserActions
            actions = []
            for row in rows:
                action = UserActions(
                    action_id=row['action_id'],
                    user_id=row['user_id'],
                    callback=row['callback'],
                    message=row['message'],
                    timestamp=row['timestamp']
                )
                actions.append(action)

            logger.info(f"Получено {len(actions)} записей")
            return actions

        except Exception as e:
            logger.error(f"Ошибка получения данных: {e}")
            return []
        finally:
            if connection:
                await connection.close()

    async def get_user_actions(self, user_id: int, limit: int = 10) -> List[UserActions]:
        """Получает действия конкретного пользователя"""
        connection = None
        try:
            connection = await self.get_connection()

            rows = await connection.fetch('''
                SELECT action_id, user_id, callback, message, timestamp
                FROM user_actions
                WHERE user_id = $1
                ORDER BY action_id DESC
                LIMIT $2;
            ''', user_id, limit)

            actions = []
            for row in rows:
                action = UserActions(
                    action_id=row['action_id'],
                    user_id=row['user_id'],
                    callback=row['callback'],
                    message=row['message'],
                    timestamp=row['timestamp']
                )
                actions.append(action)

            return actions

        except Exception as e:
            logger.error(f"Ошибка получения действий пользователя {user_id}: {e}")
            return []
        finally:
            if connection:
                await connection.close()

async def input_actions(db_manager: DatabaseManager, user_id: int, message: str, callback: str = ''):
    """Интерактивный ввод сообщений"""
    try:
        # Создаем timestamp для текущего времени
        current_timestamp = int(datetime.now().timestamp())

        data = UserActions(
            callback='',
            message=message,
            user_id=user_id,
            timestamp=current_timestamp
        )

        success = await db_manager.insert_action(data)
        if success:
            print(f"✅ Сообщение '{callback}' сохранено")
        else:
            print(f"❌ Ошибка сохранения сообщения '{message}'")

    except Exception as e:
            print(f"❌ Ошибка: {e}")

async def display_actions(db_manager: DatabaseManager):
    """Отображает все сохраненные действия"""
    print("\n📋 Получение всех записей из БД:")
    actions = await db_manager.get_all_actions()

    if not actions:
        print("Нет записей в БД")
        return

    print(f"\nНайдено {len(actions)} записей:\n")
    for action in actions:
        timestamp_str = datetime.fromtimestamp(action.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print(f"ID: {action.action_id} | User: {action.user_id} | "
              f"Message: '{action.message}' | Time: {timestamp_str}")
