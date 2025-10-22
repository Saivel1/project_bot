import asyncio
import asyncpg
import logging
import time
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime, timezone

# Настройка логирования
logger = logging.getLogger(__name__)
format = '[%(asctime)s] #%(levelname)-15s %(filename)s: %(lineno)d - %(message)s'
logging.basicConfig(level=logging.INFO, format=format)

# Конфигурация панели Marzban
MARZBAN_API_URL = "https://ivvpn.world:6655"
MARZBAN_USER = "iv"
MARZBAN_PASSWORD = "URV3dEbbpK"

# Конфигурация базы данных
DB_CONFIG = {
    'host': '127.0.0.1',           # Замените на ваш хост БД
    'port': 5432,                  # Порт PostgreSQL
    'database': 'vpn_bot_db',   # Название вашей БД
    'user': 'vpn_bot_user',          # Пользователь БД
    'password': '1234'    # Пароль БД
}

# Настройки структуры БД (настроены под вашу схему)
DB_SETTINGS = {
    'table_name': 'users',                    # Название таблицы пользователей
    'user_id_column': 'user_id',             # Колонка с ID пользователя (= username из панели)
    'username_column': 'username',            # Колонка с username (может быть пустой)
    'expire_column': 'subscription_end',      # Колонка с датой окончания подписки (bigint timestamp)
    'status_column': 'status_bot',            # Колонка со статусом бота
    'created_at_column': 'created_at'         # Колонка с временем создания
}

class MarzbanAPI:
    def __init__(self):
        self.session = None
        self.headers = {"accept": "application/json"}
        self.base_url = MARZBAN_API_URL

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

        await self.authorize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authorize(self) -> bool:
        """Авторизация в панели Marzban"""
        data = {
            "username": MARZBAN_USER,
            "password": MARZBAN_PASSWORD,
        }

        try:
            async with self.session.post(f"{self.base_url}/api/admin/token", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    self.headers["Authorization"] = f"Bearer {token}"
                    logger.info("✅ Авторизация в Marzban успешна")
                    return True
                else:
                    logger.error(f"❌ Ошибка авторизации в Marzban: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Исключение при авторизации: {e}")
            return False

    async def get_users(self) -> Optional[List[Dict]]:
        """Получение всех пользователей из панели"""
        try:
            async with self.session.get(f"{self.base_url}/api/users/", headers=self.headers) as response:
                if response.status in (200, 201):
                    result = await response.json()
                    return result.get('users', [])
                else:
                    logger.error(f"❌ Ошибка получения пользователей: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Исключение при получении пользователей: {e}")
            return None

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def __aenter__(self):
        """Создание пула подключений к БД"""
        try:
            self.pool = await asyncpg.create_pool(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                min_size=1,
                max_size=10
            )
            logger.info("✅ Подключение к базе данных установлено")
            return self
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Подключение к БД закрыто")

    async def get_user_by_panel_username(self, panel_username: str) -> Optional[Dict]:
        """Получение пользователя из БД по username из панели (= user_id в БД)"""
        try:
            # Конвертируем panel_username в число для поиска по user_id
            user_id = int(panel_username)
        except ValueError:
            logger.warning(f"⚠️ Username из панели '{panel_username}' не является числом")
            return None
            
        query = f"""
        SELECT {DB_SETTINGS['user_id_column']}, 
               {DB_SETTINGS['username_column']},
               {DB_SETTINGS['expire_column']},
               {DB_SETTINGS['status_column']}
        FROM {DB_SETTINGS['table_name']} 
        WHERE {DB_SETTINGS['user_id_column']} = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id)
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {panel_username} из БД: {e}")
            return None

    async def update_user_subscription(self, panel_username: str, expire_timestamp: int) -> bool:
        """Обновление даты окончания подписки пользователя"""
        try:
            user_id = int(panel_username)
        except ValueError:
            logger.error(f"❌ Username из панели '{panel_username}' не является числом")
            return False
            
        # В вашей БД subscription_end хранится как bigint (timestamp), не datetime
        query = f"""
        UPDATE {DB_SETTINGS['table_name']} 
        SET {DB_SETTINGS['expire_column']} = $2
        WHERE {DB_SETTINGS['user_id_column']} = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, user_id, expire_timestamp)
                updated_rows = int(result.split()[-1])
                return updated_rows > 0
        except Exception as e:
            logger.error(f"❌ Ошибка обновления пользователя {panel_username}: {e}")
            return False

    async def create_user(self, panel_username: str, expire_timestamp: int) -> bool:
        """Создание нового пользователя в БД"""
        try:
            user_id = int(panel_username)
        except ValueError:
            logger.error(f"❌ Username из панели '{panel_username}' не является числом")
            return False
            
        current_timestamp = int(time.time())
        
        query = f"""
        INSERT INTO {DB_SETTINGS['table_name']} (
            {DB_SETTINGS['user_id_column']}, 
            {DB_SETTINGS['username_column']},
            {DB_SETTINGS['status_column']},
            {DB_SETTINGS['created_at_column']},
            {DB_SETTINGS['expire_column']},
            total_spend,
            link,
            trial,
            trial_end,
            referral_count,
            first_visit_completed
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, 
                    user_id,                    # user_id
                    '',                         # username (пустой)
                    'active',                   # status_bot
                    current_timestamp,          # created_at
                    expire_timestamp,           # subscription_end
                    0,                          # total_spend
                    '',                         # link
                    'never_used',              # trial
                    0,                          # trial_end
                    0,                          # referral_count
                    False                       # first_visit_completed
                )
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя {panel_username}: {e}")
            return False

    async def get_database_stats(self) -> Dict:
        """Получение статистики из БД"""
        try:
            async with self.pool.acquire() as conn:
                # Общее количество пользователей
                total_users = await conn.fetchval(f"SELECT COUNT(*) FROM {DB_SETTINGS['table_name']}")
                
                # Пользователи с активными подписками (subscription_end > текущий timestamp)
                current_timestamp = int(time.time())
                active_users = await conn.fetchval(f"""
                    SELECT COUNT(*) FROM {DB_SETTINGS['table_name']} 
                    WHERE {DB_SETTINGS['expire_column']} > $1
                """, current_timestamp)
                
                return {
                    'total_users': total_users,
                    'active_subscriptions': active_users
                }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики БД: {e}")
            return {'total_users': 0, 'active_subscriptions': 0}

def timestamp_to_readable(timestamp: int) -> str:
    """Конвертация timestamp в читаемый формат"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

async def migrate_panel_to_database():
    """Главная функция миграции данных из панели в БД"""
    logger.info("🚀 Начинаем миграцию данных из панели Marzban в базу данных...")
    
    # Статистика
    stats = {
        'panel_users': 0,
        'users_with_subscriptions': 0,
        'users_created': 0,
        'users_updated': 0,
        'users_skipped': 0,
        'errors': 0
    }

    async with MarzbanAPI() as marzban, DatabaseManager() as db:
        
        # Получаем статистику БД до миграции
        logger.info("📊 Получаем статистику базы данных...")
        db_stats_before = await db.get_database_stats()
        logger.info(f"📈 БД до миграции: {db_stats_before['total_users']} пользователей, {db_stats_before['active_subscriptions']} активных")
        
        # Получаем пользователей из панели
        logger.info("📋 Получаем пользователей из панели Marzban...")
        panel_users = await marzban.get_users()
        
        if not panel_users:
            logger.error("❌ Не удалось получить пользователей из панели")
            return

        stats['panel_users'] = len(panel_users)
        logger.info(f"📊 Найдено {stats['panel_users']} пользователей в панели")

        # Фильтруем пользователей с активными подписками
        current_time = int(time.time())
        users_with_subs = [
            user for user in panel_users 
            if user.get('expire') and user.get('expire') > current_time
        ]
        
        stats['users_with_subscriptions'] = len(users_with_subs)
        logger.info(f"📊 Найдено {stats['users_with_subscriptions']} пользователей с активными подписками")

        # Обрабатываем каждого пользователя
        for i, panel_user in enumerate(users_with_subs, 1):
            panel_username = panel_user.get('username')  # Это будет числовой ID
            panel_expire = panel_user.get('expire')
            
            if not panel_username or not panel_expire:
                logger.warning(f"⚠️ Пользователь {i} имеет некорректные данные, пропускаем")
                stats['errors'] += 1
                continue

            logger.info(f"🔄 [{i}/{stats['users_with_subscriptions']}] Обрабатываем: {panel_username}")
            logger.info(f"   📅 Подписка до: {timestamp_to_readable(panel_expire)}")

            try:
                # Проверяем, существует ли пользователь в БД (panel_username = user_id в БД)
                db_user = await db.get_user_by_panel_username(panel_username)
                
                if db_user is None:
                    # Пользователя нет в БД - создаем нового
                    logger.info(f"➕ Создаем пользователя {panel_username} в БД")
                    
                    success = await db.create_user(panel_username, panel_expire)
                    if success:
                        stats['users_created'] += 1
                        logger.info(f"✅ Пользователь {panel_username} создан в БД")
                    else:
                        stats['errors'] += 1
                
                else:
                    # Пользователь существует - сравниваем даты
                    db_expire = db_user.get(DB_SETTINGS['expire_column'])
                    
                    if db_expire and db_expire > 0:
                        logger.info(f"   📅 В БД до: {timestamp_to_readable(db_expire)}")
                        
                        if panel_expire > db_expire:
                            # Подписка в панели длиннее - обновляем БД
                            logger.info(f"⬆️ Обновляем подписку для {panel_username}")
                            
                            success = await db.update_user_subscription(panel_username, panel_expire)
                            if success:
                                stats['users_updated'] += 1
                                logger.info(f"✅ Подписка {panel_username} обновлена в БД")
                            else:
                                stats['errors'] += 1
                        else:
                            # Подписка в БД длиннее или равна - оставляем
                            logger.info(f"⏭️ Подписка {panel_username} в БД актуальна, пропускаем")
                            stats['users_skipped'] += 1
                    else:
                        # В БД нет даты подписки или она 0 - обновляем
                        logger.info(f"⬆️ Устанавливаем подписку для {panel_username} (была пустая)")
                        
                        success = await db.update_user_subscription(panel_username, panel_expire)
                        if success:
                            stats['users_updated'] += 1
                        else:
                            stats['errors'] += 1

            except Exception as e:
                logger.error(f"❌ Ошибка при обработке пользователя {panel_username}: {e}")
                stats['errors'] += 1

            # Небольшая задержка
            await asyncio.sleep(0.1)

        # Получаем статистику БД после миграции
        db_stats_after = await db.get_database_stats()
        
        # Итоговая статистика
        logger.info(f"""
🎯 === РЕЗУЛЬТАТЫ МИГРАЦИИ ===
📊 Пользователей в панели: {stats['panel_users']}
✅ С активными подписками: {stats['users_with_subscriptions']}
➕ Создано новых: {stats['users_created']}
⬆️ Обновлено: {stats['users_updated']}
⏭️ Пропущено: {stats['users_skipped']}
❌ Ошибок: {stats['errors']}

📈 СТАТИСТИКА БД:
   До:  {db_stats_before['total_users']} всего, {db_stats_before['active_subscriptions']} активных
   После: {db_stats_after['total_users']} всего, {db_stats_after['active_subscriptions']} активных
==============================
""")

async def main():
    """Точка входа"""
    try:
        await migrate_panel_to_database()
    except KeyboardInterrupt:
        logger.info("⏹️ Миграция прервана пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    print("🔄 Скрипт миграции данных из панели Marzban в базу данных")
    print("⚠️  Убедитесь, что настроили правильные параметры БД и структуру таблиц!")
    print()
    
    # Показываем текущие настройки
    print("🔧 Текущие настройки:")
    print(f"   🔗 Панель: {MARZBAN_API_URL}")
    print(f"   🗄️  БД: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"   📋 Таблица: {DB_SETTINGS['table_name']}")
    print(f"   🔗 Соответствие: панель.username = БД.user_id")
    print(f"   📅 Колонка подписки: {DB_SETTINGS['expire_column']} (bigint timestamp)")
    print("   ✅ Создание новых пользователей включено")
    print()
    
    # Подтверждение
    response = input("Продолжить миграцию? (y/N): ").strip().lower()
    if response not in ['y', 'yes', 'да']:
        print("❌ Миграция отменена")
        exit(0)
    
    asyncio.run(main())
