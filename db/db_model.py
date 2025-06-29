import asyncpg
import asyncio
from typing import Optional, List, Tuple
from dataclasses import dataclass, asdict
import time
import logging
from datetime import datetime


# Ваши dataclasses
@dataclass(slots=True, frozen=True)
class User:
    user_id: int = 0
    username: str = ""
    status_bot: str = "active"  # Заблокирован или нет у пользователя чат бот для рассылок
    created_at: int = 0  # Будем хранить здесь timestamp и не будем его менять для БД, чтобы извлечение было прямым
    balance: int = 0  # В БД это будет total_spend
    link: str = ""  # Это ссылка на подписку или state.link
    trial: str = "never_used"
    trial_end: int = 0
    referral_count: int = 0
    first_visit_completed: bool = False
    subscription_end: int = 0


@dataclass(slots=True, frozen=True)
class UserActions:
    callback: str = ''
    message: str = ''
    user_id: int = 0
    timestamp: int = 0
    action_id: int = 0

@dataclass(slots=True, frozen=True)
class Refferal:
    who_invite: int = 0
    invited: int = 0
    bonus_status: bool = False
    created_at: int = 0
    bonus_used_at: int = 0
    status_changed_at: int = 0


@dataclass(slots=True, frozen=True)
class Payment:
    id: int = 0
    user_id: int = 0
    status: str = ''
    fail_reason: str = ''
    timestamp: int = 0
    amount: int = 0
    charge_id: str = ''

class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize_connection_pool(self):
        """Создание пула соединений с БД"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_config.db_host,
                user=self.db_config.db_user,
                password=self.db_config.db_password,
                database=self.db_config.database,
                port=self.db_config.db_port,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logging.info("Пул соединений с БД создан успешно")
        except Exception as e:
            logging.error(f"Ошибка создания пула соединений: {e}")
            raise

    async def close_pool(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
            logging.info("Пул соединений закрыт")

    async def create_tables(self):
        """Создание всех таблиц в БД"""
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255) DEFAULT '',
            status_bot VARCHAR(50) DEFAULT 'active',
            created_at BIGINT NOT NULL,
            total_spend INTEGER DEFAULT 0,
            link TEXT DEFAULT '',
            trial VARCHAR(50) DEFAULT 'never_used',
            trial_end BIGINT DEFAULT 0,
            referral_count INTEGER DEFAULT 0,
            first_visit_completed BOOLEAN DEFAULT FALSE,
            subscription_end BIGINT DEFAULT 0
        );
        """

        create_user_actions_table = """
        CREATE TABLE IF NOT EXISTS user_actions (
            action_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            callback VARCHAR(255) DEFAULT '',
            message TEXT DEFAULT '',
            timestamp BIGINT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """

        create_refferals_table = """
        CREATE TABLE IF NOT EXISTS refferals (
            id SERIAL PRIMARY KEY,
            who_invite BIGINT NOT NULL,
            invited BIGINT NOT NULL UNIQUE,
            bonus_status BOOLEAN DEFAULT FALSE,
            created_at BIGINT NOT NULL,
            bonus_used_at BIGINT DEFAULT 0,
            status_changed_at BIGINT DEFAULT 0,
            FOREIGN KEY (who_invite) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (invited) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(who_invite, invited)
        );
        """

        create_payments_table = """
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            status VARCHAR(50) NOT NULL,
            fail_reason TEXT DEFAULT '',
            timestamp BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            charge_id VARCHAR(255) DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """

        # Создание индексов для оптимизации запросов
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON user_actions(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_refferals_who_invite ON refferals(who_invite);",
            "CREATE INDEX IF NOT EXISTS idx_refferals_invited ON refferals(invited);",
            "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);"
        ]

        async with self.pool.acquire() as conn:
            try:
                # Создаем таблицы
                await conn.execute(create_users_table)
                await conn.execute(create_user_actions_table)
                await conn.execute(create_refferals_table)
                await conn.execute(create_payments_table)

                # Создаем индексы
                for index_query in create_indexes:
                    await conn.execute(index_query)

                logging.info("Все таблицы и индексы созданы успешно")
            except Exception as e:
                logging.error(f"Ошибка создания таблиц: {e}")
                raise

    # ===========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
    # ===========================================

    async def create_user(self, user: User) -> bool:
        """Создание нового пользователя"""
        query = """
        INSERT INTO users (user_id, username, status_bot, created_at,
                          total_spend, link, trial, trial_end,
                          referral_count, first_visit_completed, subscription_end)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (user_id) DO NOTHING
        """

        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(
                    query, user.user_id, user.username,
                    user.status_bot, user.created_at, user.balance,
                    user.link, user.trial, user.trial_end,
                    user.referral_count, user.first_visit_completed, user.subscription_end
                )
                return "INSERT" in result
            except Exception as e:
                logging.error(f"Ошибка создания пользователя {user.user_id}: {e}")
                return False

    async def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        query = """
        SELECT user_id, username, status_bot, created_at,
               total_spend, link, trial, trial_end, referral_count,
               first_visit_completed, subscription_end
        FROM users WHERE user_id = $1
        """

        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, user_id)
                if row:
                    return User(
                        user_id=row['user_id'],
                        username=row['username'],
                        status_bot=row['status_bot'],
                        created_at=row['created_at'],
                        balance=row['total_spend'],  # Маппинг total_spend -> balance
                        link=row['link'],
                        trial=row['trial'],
                        trial_end=row['trial_end'],
                        referral_count=row['referral_count'],
                        first_visit_completed=row['first_visit_completed'],
                        subscription_end=row['subscription_end']
                    )
                return None
            except Exception as e:
                logging.error(f"Ошибка получения пользователя {user_id}: {e}")
                return None

    async def update_user(self, user: User) -> bool:
        """Обновление данных пользователя"""
        query = """
        UPDATE users SET
            username = $2, status_bot = $3,
            total_spend = $4, link = $5, trial = $6, trial_end = $7,
            referral_count = $8, first_visit_completed = $9, subscription_end = $10
        WHERE user_id = $1
        """

        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(
                    query, user.user_id, user.username,
                    user.status_bot, user.balance, user.link,
                    user.trial, user.trial_end, user.referral_count,
                    user.first_visit_completed, user.subscription_end
                )
                return "UPDATE" in result
            except Exception as e:
                logging.error(f"Ошибка обновления пользователя {user.user_id}: {e}")
                return False

    # ================================
    # Тут мы помещаем значения, которые будут дэфолтными
    # ================================
    async def get_or_create_user(self, user_id: int, username: str = "") -> User:
        """Получить пользователя или создать если не существует"""
        user = await self.get_user(user_id)
        if user:
            return user

        # seting those values as default
        # Создаем нового пользователя
        new_user = User(
            user_id=user_id,
            username=username,
            created_at=int(time.time()),
            trial='never_used',
            first_visit_completed=False
        )

        success = await self.create_user(new_user)
        if success:
            return new_user
        else:
            # Если создание не удалось, пытаемся получить еще раз
            return await self.get_user(user_id)

    # ===========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ДЕЙСТВИЯМИ ПОЛЬЗОВАТЕЛЕЙ
    # ===========================================

    async def log_user_action(self, user_id: int, callback: str = "", message: str = "") -> bool:
        """Логирование действия пользователя, имеется ввиду вставка записи в таблицу user_actions"""
        query = """
        INSERT INTO user_actions (user_id, callback, message, timestamp)
        VALUES ($1, $2, $3, $4)
        """
        current_date = int(datetime.timestamp(datetime.now()))
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, user_id, callback, message, current_date)
                return True
            except Exception as e:
                logging.error(f"Ошибка логирования действия пользователя {user_id}: {e}")
                return False

    async def get_user_actions(self, user_id: int, limit: int = 100) -> List[UserActions]:
        """Получение последних действий пользователя"""
        query = """
        SELECT action_id, user_id, callback, message, timestamp
        FROM user_actions
        WHERE user_id = $1
        ORDER BY timestamp DESC
        LIMIT $2
        """

        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, user_id, limit)
                return [
                    UserActions(
                        action_id=row['action_id'],
                        user_id=row['user_id'],
                        callback=row['callback'],
                        message=row['message'],
                        timestamp=row['timestamp']
                    )
                    for row in rows
                ]
            except Exception as e:
                logging.error(f"Ошибка получения действий пользователя {user_id}: {e}")
                return []

    # ===========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С РЕФЕРАЛАМИ
    # ===========================================
    async def check_referral_exists(self, who_invite: int, invited: int) -> bool:
        """Проверяет существование реферальной связи между пользователями"""
        query = """
        SELECT EXISTS(
        SELECT 1 FROM refferals
        WHERE who_invite = $1 AND invited = $2
        )
        """

        async with self.pool.acquire() as conn:
            try:
                exists = await conn.fetchval(query, who_invite, invited)
                return exists
            except Exception as e:
                logging.error(f"Ошибка проверки существования реферала {who_invite} -> {invited}: {e}")
                return False

    async def check_user_is_inviter(self, user_id: int) -> bool:
        """Проверяет является ли пользователь пригласившим (есть ли записи где он who_invite)"""
        query = """
        SELECT EXISTS(
            SELECT 1 FROM refferals
            WHERE who_invite = $1
        )
        """

        async with self.pool.acquire() as conn:
            try:
                exists = await conn.fetchval(query, user_id)
                return exists
            except Exception as e:
                logging.error(f"Ошибка проверки статуса пригласившего для пользователя {user_id}: {e}")
                return False

    async def create_referral(self, who_invite: int, invited: int) -> bool:
        reverse_exists = await self.check_referral_exists(invited, who_invite)
        if reverse_exists:
            logging.warning(f"Обратная связь уже существует: {invited} -> {who_invite}")
            return False
        invited_is_inviter = await self.check_user_is_inviter(invited)
        if invited_is_inviter:
            logging.warning(f"Пользователь {invited} уже является пригласившим, не может быть приглашен")
            return False
        """Создание реферальной связи"""
        query = """
        INSERT INTO refferals (who_invite, invited, created_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (who_invite, invited) DO NOTHING
        """

        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(query, who_invite, invited, int(time.time()))
                return "INSERT" in result
            except Exception as e:
                logging.error(f"Ошибка создания реферала {who_invite} -> {invited}: {e}")
                return False

    async def count_unused_referrals(self, user_id: int) -> int:
        """Считает количество неиспользованных рефералов (bonus_status = TRUE)"""
        query = """
        SELECT COUNT(*) FROM refferals
        WHERE who_invite = $1 AND bonus_status = TRUE
        """

        async with self.pool.acquire() as conn:
            try:
                count = await conn.fetchval(query, user_id)
                logging.info(f"Найдено {count} неиспользованных рефералов для пользователя {user_id}")
                return count or 0
            except Exception as e:
                logging.error(f"Ошибка подсчета неиспользованных рефералов для пользователя {user_id}: {e}")
                return 0

    async def mark_referrals_as_used(self, user_id: int) -> int:
        """Массово помечает рефералов как использованных (bonus_status = NULL)"""
        current_time = int(time.time())

        query = """
        UPDATE refferals
        SET
            bonus_status = NULL,
            bonus_used_at = $2,
            status_changed_at = $2
        WHERE
            who_invite = $1
            AND bonus_status = TRUE
        """

        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(query, user_id, current_time)
                updated_count = int(result.split()[-1]) if "UPDATE" in result else 0

                logging.info(f"Помечено как использованные {updated_count} рефералов для пользователя {user_id}")
                return updated_count

            except Exception as e:
                logging.error(f"Ошибка массового обновления рефералов для пользователя {user_id}: {e}")
                return 0


    async def get_user_referrals(self, user_id: int) -> List[Refferal]:
        """Получение всех рефералов пользователя"""
        query = """
        SELECT who_invite, invited, bonus_status, created_at,
               bonus_used_at, status_changed_at
        FROM refferals
        WHERE who_invite = $1
        ORDER BY created_at DESC
        """

        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, user_id)
                return [
                    Refferal(
                        who_invite=row['who_invite'],
                        invited=row['invited'],
                        bonus_status=row['bonus_status'],
                        created_at=row['created_at'],
                        bonus_used_at=row['bonus_used_at'],
                        status_changed_at=row['status_changed_at']
                    )
                    for row in rows
                ]
            except Exception as e:
                logging.error(f"Ошибка получения рефералов пользователя {user_id}: {e}")
                return []

    async def update_referral_bonus(self, invited: int) -> bool:
        """Обновление статуса бонуса реферала"""
        current_time = int(time.time())

        query = """
        UPDATE refferals SET
            bonus_status = TRUE,
            status_changed_at = $2,
            bonus_used_at = CASE WHEN bonus_status = FALSE THEN $2 ELSE bonus_used_at END
        WHERE invited = $1 AND bonus_status = FALSE
        """

        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(query, invited, current_time)
                return "UPDATE" in result
            except Exception as e:
                logging.error(f"Ошибка обновления бонуса реферала для invited {invited}: {e}")
                return False

    # ===========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ПЛАТЕЖАМИ
    # ===========================================

    async def create_payment(self, user_id: int, amount: int, status: str = "pending", charge_id: str = "") -> Optional[int]:
        """Создание записи о платеже"""
        query = """
        INSERT INTO payments (user_id, amount, status, timestamp, charge_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """

        async with self.pool.acquire() as conn:
            try:
                payment_id = await conn.fetchval(query, user_id, amount, status, int(time.time()), charge_id)
                return payment_id
            except Exception as e:
                logging.error(f"Ошибка создания платежа для пользователя {user_id}: {e}")
                return None



# Пример инициализации и использования
async def init_database(db_config):
    """Инициализация базы данных"""
    db_manager = DatabaseManager(db_config)
    await db_manager.create_pool()
    await db_manager.create_tables()
    return db_manager