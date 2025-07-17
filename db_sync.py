#!/usr/bin/env python3
"""
Обновление ссылок подписки в PostgreSQL базе данных
Marzban username == user_id в БД
Колонка с ссылками называется 'link'
"""

import asyncpg
import aiohttp
import asyncio
from datetime import datetime
import sys

# Настройки PostgreSQL
PG_HOST = "127.0.0.1"
PG_PORT = 5432
PG_USER = "vpn_bot_user"
PG_PASSWORD = "1234"
PG_DATABASE = "vpn_bot_db"

# Настройки Marzban
NEW_MARZBAN_URL = "https://ivvpn.world:6655"
NEW_MARZBAN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpdiIsImFjY2VzcyI6InN1ZG8iLCJpYXQiOjE3NTI2NzM0ODAsImV4cCI6MTc1Mjc1OTg4MH0.bpzpn3WYl6BiJdH2IVWDHPNpyWkYS8g5DDdAVQ-5c38"

# Домены для замены
OLD_DOMAIN = "ivvpn.digital"
NEW_DOMAIN = "ivvpn.world"

async def get_db_connection():
    """Создать подключение к PostgreSQL"""
    try:
        conn = await asyncpg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return None

async def test_connection():
    """Тест подключения к базе данных"""
    print("🔍 Тестируем подключение к PostgreSQL...")
    
    conn = await get_db_connection()
    if not conn:
        return False
    
    try:
        # Тест запроса
        version = await conn.fetchval("SELECT version()")
        print(f"✅ Успешное подключение!")
        print(f"   PostgreSQL: {version[:80]}...")
        
        # Проверить таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        table_names = [row['table_name'] for row in tables]
        print(f"📊 Найдены таблицы: {table_names}")
        
        # Проверить колонки таблицы users
        if 'users' in table_names:
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """)
            
            column_names = [row['column_name'] for row in columns]
            print(f"📋 Колонки таблицы users: {column_names}")
            
            # Проверить нужные колонки
            if 'user_id' in column_names:
                print("✅ Колонка 'user_id' найдена")
            else:
                print("❌ Колонка 'user_id' НЕ найдена")
                
            if 'link' in column_names:
                print("✅ Колонка 'link' найдена")
            else:
                print("❌ Колонка 'link' НЕ найдена")
                
            # Показать примеры данных
            sample = await conn.fetch("SELECT user_id, link FROM users LIMIT 3")
            print(f"\n📝 Примеры данных:")
            for row in sample:
                print(f"   user_id: {row['user_id']}, link: {row['link']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        await conn.close()
        return False

async def backup_users_table():
    """Создать резервную копию таблицы users"""
    conn = await get_db_connection()
    if not conn:
        return False
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"users_backup_{timestamp}"
        
        # Создать таблицу-копию
        await conn.execute(f"""
            CREATE TABLE {backup_table} AS 
            SELECT * FROM users
        """)
        
        # Подсчитать записи
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {backup_table}")
        
        print(f"✅ Резервная копия создана: {backup_table} ({count} записей)")
        await conn.close()
        return backup_table
        
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        await conn.close()
        return False

async def get_user_from_panel(session, user_id):
    """Получить ссылку подписки пользователя из новой панели Marzban
    user_id используется как username в Marzban API
    """
    headers = {"Authorization": f"Bearer {NEW_MARZBAN_TOKEN}"}
    
    try:
        # Используем user_id как username для Marzban API
        async with session.get(
            f"{NEW_MARZBAN_URL}/api/user/{user_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                user_data = await response.json()
                return user_data.get("subscription_url")
            else:
                return None
    except Exception as e:
        print(f"❌ Ошибка получения user_id {user_id}: {e}")
        return None

async def check_subscription_links():
    """Проверить текущее состояние ссылок подписки"""
    conn = await get_db_connection()
    if not conn:
        return
    
    try:
        # Подсчитать записи по доменам
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE link LIKE $1) as old_domain,
                COUNT(*) FILTER (WHERE link LIKE $2) as new_domain,
                COUNT(*) FILTER (WHERE link IS NULL OR link = '') as empty_links
            FROM users
        """, f"%{OLD_DOMAIN}%", f"%{NEW_DOMAIN}%")
        
        print(f"📊 Статистика ссылок подписки:")
        print(f"   Всего пользователей: {stats['total']}")
        print(f"   Старый домен ({OLD_DOMAIN}): {stats['old_domain']}")
        print(f"   Новый домен ({NEW_DOMAIN}): {stats['new_domain']}")
        print(f"   Пустые ссылки: {stats['empty_links']}")
        
        # Показать примеры
        if stats['old_domain'] > 0:
            print(f"\n📝 Примеры записей со старым доменом:")
            examples = await conn.fetch("""
                SELECT user_id, link 
                FROM users 
                WHERE link LIKE $1 
                LIMIT 5
            """, f"%{OLD_DOMAIN}%")
            
            for row in examples:
                print(f"   user_id: {row['user_id']}, link: {row['link']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        await conn.close()

async def update_links_from_panel():
    """Обновить ссылки получением из новой панели Marzban"""
    
    # Создать резервную копию
    backup_table = await backup_users_table()
    if not backup_table:
        print("❌ Не удалось создать резервную копию. Остановка.")
        return False
    
    conn = await get_db_connection()
    if not conn:
        return False
    
    try:
        # Получить всех пользователей из БД
        users = await conn.fetch("SELECT user_id FROM users ORDER BY user_id")
        user_ids = [str(row['user_id']) for row in users]  # Конвертируем в строки
        
        print(f"📊 Пользователей в БД: {len(user_ids)}")
        
        if not user_ids:
            print("ℹ️  Пользователи в БД не найдены")
            await conn.close()
            return True
        
        # Показать примеры user_id
        print(f"📝 Примеры user_id: {user_ids[:5]}")
        
        # Подтверждение обновления
        confirm = input(f"\n❓ Обновить ссылки для {len(user_ids)} пользователей из новой панели? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Отменено пользователем")
            await conn.close()
            return False
        
        # Создать HTTP сессию
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            updated_count = 0
            not_found_count = 0
            error_count = 0
            
            # Начать транзакцию
            async with conn.transaction():
                for i, user_id in enumerate(user_ids, 1):
                    print(f"[{i}/{len(user_ids)}] Обрабатываем user_id: {user_id}...")
                    
                    # Получить реальную ссылку из новой панели (user_id = username в Marzban)
                    new_link = await get_user_from_panel(session, user_id)
                    
                    if new_link:
                        # Обновить в БД
                        await conn.execute("""
                            UPDATE users 
                            SET link = $1 
                            WHERE user_id = $2
                        """, new_link, int(user_id))
                        
                        updated_count += 1
                        print(f"✅ user_id {user_id}: ссылка обновлена")
                        
                    elif new_link is None:
                        not_found_count += 1
                        print(f"⚠️  user_id {user_id}: не найден в новой панели")
                    else:
                        error_count += 1
                        print(f"❌ user_id {user_id}: ошибка получения данных")
                    
                    # Пауза между запросами
                    await asyncio.sleep(0.2)
        
        print(f"\n🎉 Обновление завершено!")
        print(f"✅ Успешно обновлено: {updated_count}")
        print(f"⚠️  Не найдено в панели: {not_found_count}")
        print(f"❌ Ошибки: {error_count}")
        print(f"💾 Резервная копия: {backup_table}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        await conn.close()
        return False

async def simple_domain_replacement():
    """Простая замена домена в ссылках"""
    
    # Создать резервную копию
    backup_table = await backup_users_table()
    if not backup_table:
        return False
    
    conn = await get_db_connection()
    if not conn:
        return False
    
    try:
        # Найти записи со старым доменом
        old_records = await conn.fetch("""
            SELECT user_id, link 
            FROM users 
            WHERE link LIKE $1
        """, f"%{OLD_DOMAIN}%")
        
        print(f"🔍 Найдено записей для замены домена: {len(old_records)}")
        
        if not old_records:
            print("ℹ️  Записи для замены не найдены")
            await conn.close()
            return True
        
        # Показать примеры
        print(f"\n📝 Примеры записей для замены:")
        for i, row in enumerate(old_records[:3]):
            print(f"   user_id: {row['user_id']}, link: {row['link']}")
        if len(old_records) > 3:
            print(f"   ... и еще {len(old_records) - 3} записей")
        
        confirm = input(f"\n❓ Заменить домен в {len(old_records)} записях? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Отменено")
            await conn.close()
            return False
        
        # Обновить записи в транзакции
        async with conn.transaction():
            updated_count = 0
            for row in old_records:
                user_id = row['user_id']
                old_url = row['link']
                new_url = old_url.replace(OLD_DOMAIN, NEW_DOMAIN + ":6655")
                
                await conn.execute("""
                    UPDATE users 
                    SET link = $1 
                    WHERE user_id = $2
                """, new_url, user_id)
                
                updated_count += 1
                print(f"✅ user_id {user_id}: {old_url} → {new_url}")
        
        print(f"\n🎉 Заменен домен у {updated_count} пользователей")
        print(f"💾 Резервная копия: {backup_table}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await conn.close()
        return False

async def check_users_in_panel():
    """Проверить какие пользователи есть в новой панели Marzban"""
    conn = await get_db_connection()
    if not conn:
        return
    
    try:
        # Получить всех пользователей из БД
        users = await conn.fetch("SELECT user_id FROM users ORDER BY user_id")
        user_ids = [str(row['user_id']) for row in users]
        
        print(f"📊 Проверяем {len(user_ids)} пользователей в новой панели...")
        print(f"📝 Примеры user_id: {user_ids[:5]}")
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            found_count = 0
            not_found_count = 0
            
            for user_id in user_ids:
                # Используем user_id как username в Marzban API
                subscription_url = await get_user_from_panel(session, user_id)
                
                if subscription_url:
                    found_count += 1
                    print(f"✅ user_id {user_id}: есть в панели Marzban")
                else:
                    not_found_count += 1
                    print(f"❌ user_id {user_id}: НЕТ в панели Marzban")
                
                await asyncio.sleep(0.1)
        
        print(f"\n📈 Результат проверки:")
        print(f"✅ Найдено в панели: {found_count}")
        print(f"❌ Не найдено: {not_found_count}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        await conn.close()

async def show_backup_tables():
    """Показать доступные резервные копии"""
    conn = await get_db_connection()
    if not conn:
        return
    
    try:
        # Найти таблицы бэкапов
        backup_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'users_backup_%'
            ORDER BY table_name DESC
        """)
        
        if backup_tables:
            print(f"💾 Доступные резервные копии:")
            for row in backup_tables:
                table_name = row['table_name']
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                print(f"   {table_name} ({count} записей)")
        else:
            print("ℹ️  Резервные копии не найдены")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await conn.close()

async def update_specific_users(user_ids):
    """Обновить ссылки для конкретных пользователей"""
    backup_table = await backup_users_table()
    if not backup_table:
        return False
    
    conn = await get_db_connection()
    if not conn:
        return False
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            updated_count = 0
            
            for user_id in user_ids:
                print(f"📤 Обрабатываем user_id: {user_id}...")
                
                # Получить реальную ссылку из панели (user_id = username в Marzban)
                new_link = await get_user_from_panel(session, user_id)
                
                if new_link:
                    # Обновить в БД
                    await conn.execute("""
                        UPDATE users 
                        SET link = $1 
                        WHERE user_id = $2
                    """, new_link, int(user_id))
                    
                    updated_count += 1
                    print(f"✅ user_id {user_id}: ссылка обновлена из панели")
                else:
                    print(f"❌ user_id {user_id}: не удалось получить ссылку")
                
                await asyncio.sleep(0.2)
        
        print(f"\n🎉 Обновлено {updated_count} пользователей")
        print(f"💾 Резервная копия: {backup_table}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await conn.close()
        return False

async def main():
    """Главная функция"""
    print("🔄 Обновление ссылок подписки в PostgreSQL")
    print(f"🗄️  База данных: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    print(f"🌐 Новая панель: {NEW_MARZBAN_URL}")
    print(f"🔗 Соответствие: user_id (БД) = username (Marzban)")
    print("="*60)
    
    # Обработка аргументов командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            await test_connection()
            return
        elif sys.argv[1] == "check":
            await check_subscription_links()
            return
        elif sys.argv[1] == "panel":
            await check_users_in_panel()
            return
        elif sys.argv[1] == "domain":
            await simple_domain_replacement()
            return
        elif sys.argv[1] == "backups":
            await show_backup_tables()
            return
        elif sys.argv[1] == "users":
            if len(sys.argv) < 3:
                print("❌ Укажите user_id: python script.py users 123456 789012")
                return
            user_ids = sys.argv[2:]
            await update_specific_users(user_ids)
            return
    
    # Интерактивное меню
    print("1. Тест подключения к БД")
    print("2. Проверить текущее состояние ссылок")
    print("3. Проверить пользователей в новой панели")
    print("4. Обновить ссылки получением из новой панели (рекомендуется)")
    print("5. Простая замена домена")
    print("6. Показать резервные копии")
    
    choice = input("\nВыберите действие (1-6): ")
    
    if choice == "1":
        await test_connection()
    elif choice == "2":
        await check_subscription_links()
    elif choice == "3":
        await check_users_in_panel()
    elif choice == "4":
        await update_links_from_panel()
    elif choice == "5":
        await simple_domain_replacement()
    elif choice == "6":
        await show_backup_tables()
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    print("🐘 Скрипт для обновления ссылок в PostgreSQL")
    print("📋 user_id из БД используется как username в Marzban API")
    asyncio.run(main())
