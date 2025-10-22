import asyncio
import logging
import time
from typing import Dict, List, Set, Optional
import aiohttp
from datetime import datetime

# Настройка логирования
logger = logging.getLogger(__name__)
format = '[%(asctime)s] #%(levelname)-15s %(filename)s: %(lineno)d - %(message)s'
logging.basicConfig(level=logging.INFO, format=format)

# Конфигурация панелей
PANEL_1_CONFIG = {
    'name': 'Основная панель (World)',
    'url': 'https://ivvpn.world:6655',
    'username': 'iv',
    'password': 'URV3dEbbpK'
}

PANEL_2_CONFIG = {
    'name': 'Синхронизируемая панель (Moba)',
    'url': 'https://mob.ivvpn.world:8443',
    'username': 'iv',
    'password': 'OoRmc1872C3a'
}

class MarzbanPanel:
    """Класс для работы с панелью Marzban"""
    
    def __init__(self, config: Dict, panel_name: str):
        self.config = config
        self.panel_name = panel_name
        self.session = None
        self.headers = {"accept": "application/json"}
        self.base_url = config['url']

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

        success = await self.authorize()
        if not success:
            raise Exception(f"Не удалось авторизоваться в {self.panel_name}")
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authorize(self) -> bool:
        """Авторизация в панели"""
        data = {
            "username": self.config['username'],
            "password": self.config['password'],
        }

        try:
            async with self.session.post(f"{self.base_url}/api/admin/token", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    self.headers["Authorization"] = f"Bearer {token}"
                    logger.info(f"✅ Авторизация в {self.panel_name} успешна")
                    return True
                else:
                    logger.error(f"❌ Ошибка авторизации в {self.panel_name}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Исключение при авторизации в {self.panel_name}: {e}")
            return False

    async def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей"""
        try:
            async with self.session.get(f"{self.base_url}/api/users/", headers=self.headers) as response:
                if response.status in (200, 201):
                    result = await response.json()
                    users = result.get('users', [])
                    logger.info(f"📊 {self.panel_name}: получено {len(users)} пользователей")
                    return users
                else:
                    logger.error(f"❌ Ошибка получения пользователей из {self.panel_name}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении пользователей из {self.panel_name}: {e}")
            return []

    async def get_user(self, username: str) -> Optional[Dict]:
        """Получение данных конкретного пользователя"""
        try:
            async with self.session.get(f"{self.base_url}/api/user/{username}", headers=self.headers) as response:
                if response.status in (200, 201):
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logger.warning(f"⚠️ Ошибка получения пользователя {username} из {self.panel_name}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Исключение при получении пользователя {username} из {self.panel_name}: {e}")
            return None

    async def create_user(self, username: str, user_data: Dict) -> bool:
        """Создание пользователя"""
        data = {
            "username": username,
            "proxies": user_data.get("proxies", {"vless": {"flow": "xtls-rprx-vision"}}),
            "inbounds": user_data.get("inbounds", {"vless": ["VLESS TCP REALITY"]}),
            "expire": user_data.get("expire", 0),
            "data_limit": user_data.get("data_limit", 0),
            "status": user_data.get("status", "active")
        }

        try:
            async with self.session.post(f"{self.base_url}/api/user/", headers=self.headers, json=data) as response:
                if response.status in (200, 201):
                    logger.info(f"✅ Пользователь {username} создан в {self.panel_name}")
                    return True
                else:
                    logger.error(f"❌ Ошибка создания пользователя {username} в {self.panel_name}: {response.status}")
                    response_text = await response.text()
                    logger.error(f"   Ответ сервера: {response_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Исключение при создании пользователя {username} в {self.panel_name}: {e}")
            return False

    async def update_user_expire(self, username: str, expire_time: int) -> bool:
        """Обновление времени окончания подписки пользователя"""
        data = {"expire": expire_time}

        try:
            async with self.session.put(f"{self.base_url}/api/user/{username}", headers=self.headers, json=data) as response:
                if response.status in (200, 201):
                    logger.info(f"✅ Дата окончания подписки для {username} обновлена в {self.panel_name}")
                    return True
                else:
                    logger.error(f"❌ Ошибка обновления подписки {username} в {self.panel_name}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Исключение при обновлении подписки {username} в {self.panel_name}: {e}")
            return False

    async def delete_user(self, username: str) -> bool:
        """Удаление пользователя"""
        try:
            async with self.session.delete(f"{self.base_url}/api/user/{username}", headers=self.headers) as response:
                if response.status in (200, 201):
                    logger.info(f"✅ Пользователь {username} удален из {self.panel_name}")
                    return True
                else:
                    logger.error(f"❌ Ошибка удаления пользователя {username} из {self.panel_name}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Исключение при удалении пользователя {username} из {self.panel_name}: {e}")
            return False


class PanelSynchronizer:
    """Класс для синхронизации панелей"""
    
    def __init__(self):
        self.panel_1 = None  # Основная панель
        self.panel_2 = None  # Синхронизируемая панель
        
    async def __aenter__(self):
        self.panel_1 = await MarzbanPanel(PANEL_1_CONFIG, "Панель 1 (Основная)").__aenter__()
        self.panel_2 = await MarzbanPanel(PANEL_2_CONFIG, "Панель 2 (Синхронизируемая)").__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.panel_1:
            await self.panel_1.__aexit__(exc_type, exc_val, exc_tb)
        if self.panel_2:
            await self.panel_2.__aexit__(exc_type, exc_val, exc_tb)

    def timestamp_to_readable(self, timestamp) -> str:
        """Конвертация timestamp в читаемый формат"""
        if timestamp is None or timestamp == 0:
            return "Без ограничений"
        try:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except (TypeError, ValueError, OSError):
            return f"Некорректная дата ({timestamp})"

    async def full_sync(self, dry_run: bool = False) -> Dict:
        """Полная синхронизация панели 2 с панелью 1"""
        logger.info("🚀 Начинаем полную синхронизацию панелей...")
        
        if dry_run:
            logger.info("🔍 РЕЖИМ ПРЕДПРОСМОТРА - изменения не будут применены")
        
        stats = {
            'users_to_create': 0,
            'users_to_update': 0,
            'users_to_delete': 0,
            'users_created': 0,
            'users_updated': 0,
            'users_deleted': 0,
            'errors': 0,
            'actions': []
        }

        # Получаем пользователей с обеих панелей
        logger.info("📋 Получаем данные пользователей...")
        panel_1_users = await self.panel_1.get_all_users()
        panel_2_users = await self.panel_2.get_all_users()

        # Создаем словари для быстрого поиска
        panel_1_dict = {user['username']: user for user in panel_1_users}
        panel_2_dict = {user['username']: user for user in panel_2_users}

        panel_1_usernames = set(panel_1_dict.keys())
        panel_2_usernames = set(panel_2_dict.keys())

        logger.info(f"📊 Панель 1: {len(panel_1_usernames)} пользователей")
        logger.info(f"📊 Панель 2: {len(panel_2_usernames)} пользователей")

        # 1. Пользователи для создания (есть в панели 1, нет в панели 2)
        users_to_create = panel_1_usernames - panel_2_usernames
        stats['users_to_create'] = len(users_to_create)
        
        if users_to_create:
            logger.info(f"➕ Нужно создать {len(users_to_create)} пользователей")
            for username in users_to_create:
                user_data = panel_1_dict[username]
                expire_time = user_data.get('expire')
                
                # Нормализуем значение expire
                expire_time = expire_time if expire_time is not None else 0
                
                action = {
                    'type': 'create',
                    'username': username,
                    'expire': expire_time,
                    'expire_readable': self.timestamp_to_readable(expire_time)
                }
                stats['actions'].append(action)
                
                logger.info(f"   📝 Создать: {username} (подписка до: {action['expire_readable']})")
                
                if not dry_run:
                    success = await self.panel_2.create_user(username, user_data)
                    if success:
                        stats['users_created'] += 1
                    else:
                        stats['errors'] += 1
                    
                    # Небольшая задержка между запросами
                    await asyncio.sleep(0.2)

        # 2. Пользователи для обновления (есть в обеих панелях, но разные даты)
        common_users = panel_1_usernames & panel_2_usernames
        users_to_update = []
        
        for username in common_users:
            panel_1_expire = panel_1_dict[username].get('expire')
            panel_2_expire = panel_2_dict[username].get('expire')
            
            # Нормализуем значения (None -> 0)
            panel_1_expire = panel_1_expire if panel_1_expire is not None else 0
            panel_2_expire = panel_2_expire if panel_2_expire is not None else 0
            
            if panel_1_expire != panel_2_expire:
                users_to_update.append({
                    'username': username,
                    'panel_1_expire': panel_1_expire,
                    'panel_2_expire': panel_2_expire
                })

        stats['users_to_update'] = len(users_to_update)
        
        if users_to_update:
            logger.info(f"🔄 Нужно обновить {len(users_to_update)} пользователей")
            for user_info in users_to_update:
                username = user_info['username']
                new_expire = user_info['panel_1_expire']
                old_expire = user_info['panel_2_expire']
                
                action = {
                    'type': 'update',
                    'username': username,
                    'old_expire': old_expire,
                    'new_expire': new_expire,
                    'old_expire_readable': self.timestamp_to_readable(old_expire),
                    'new_expire_readable': self.timestamp_to_readable(new_expire)
                }
                stats['actions'].append(action)
                
                logger.info(f"   🔄 Обновить: {username}")
                logger.info(f"      Было: {action['old_expire_readable']}")
                logger.info(f"      Стало: {action['new_expire_readable']}")
                
                if not dry_run:
                    success = await self.panel_2.update_user_expire(username, new_expire)
                    if success:
                        stats['users_updated'] += 1
                    else:
                        stats['errors'] += 1
                    
                    await asyncio.sleep(0.1)

        # 3. Пользователи для удаления (есть в панели 2, нет в панели 1)
        users_to_delete = panel_2_usernames - panel_1_usernames
        stats['users_to_delete'] = len(users_to_delete)
        
        if users_to_delete:
            logger.info(f"🗑️ Нужно удалить {len(users_to_delete)} пользователей")
            for username in users_to_delete:
                user_data = panel_2_dict[username]
                expire_time = user_data.get('expire')
                
                # Нормализуем значение expire
                expire_time = expire_time if expire_time is not None else 0
                
                action = {
                    'type': 'delete',
                    'username': username,
                    'expire': expire_time,
                    'expire_readable': self.timestamp_to_readable(expire_time)
                }
                stats['actions'].append(action)
                
                logger.info(f"   🗑️ Удалить: {username} (подписка была до: {action['expire_readable']})")
                
                if not dry_run:
                    success = await self.panel_2.delete_user(username)
                    if success:
                        stats['users_deleted'] += 1
                    else:
                        stats['errors'] += 1
                    
                    await asyncio.sleep(0.1)

        return stats

    async def sync_user(self, username: str, dry_run: bool = False) -> Dict:
        """Синхронизация конкретного пользователя"""
        logger.info(f"🔄 Синхронизация пользователя: {username}")
        
        if dry_run:
            logger.info("🔍 РЕЖИМ ПРЕДПРОСМОТРА")
        
        # Получаем данные пользователя с основной панели
        panel_1_user = await self.panel_1.get_user(username)
        if not panel_1_user:
            return {
                'success': False,
                'message': f"❌ Пользователь {username} не найден в основной панели",
                'action': 'none'
            }

        # Получаем данные пользователя со второй панели
        panel_2_user = await self.panel_2.get_user(username)
        
        if not panel_2_user:
            # Пользователя нет во второй панели - создаем
            logger.info(f"➕ Создаем пользователя {username} во второй панели")
            
            if not dry_run:
                success = await self.panel_2.create_user(username, panel_1_user)
                if success:
                    return {
                        'success': True,
                        'message': f"✅ Пользователь {username} создан во второй панели",
                        'action': 'created'
                    }
                else:
                    return {
                        'success': False,
                        'message': f"❌ Ошибка создания пользователя {username} во второй панели",
                        'action': 'error'
                    }
            else:
                return {
                    'success': True,
                    'message': f"🔍 [ПРЕДПРОСМОТР] Будет создан пользователь {username}",
                    'action': 'would_create'
                }
        else:
            # Пользователь есть в обеих панелях - проверяем даты
            panel_1_expire = panel_1_user.get('expire')
            panel_2_expire = panel_2_user.get('expire')
            
            # Нормализуем значения (None -> 0)
            panel_1_expire = panel_1_expire if panel_1_expire is not None else 0
            panel_2_expire = panel_2_expire if panel_2_expire is not None else 0
            
            if panel_1_expire != panel_2_expire:
                logger.info(f"🔄 Обновляем дату подписки для {username}")
                logger.info(f"   Панель 1: {self.timestamp_to_readable(panel_1_expire)}")
                logger.info(f"   Панель 2: {self.timestamp_to_readable(panel_2_expire)}")
                
                if not dry_run:
                    success = await self.panel_2.update_user_expire(username, panel_1_expire)
                    if success:
                        return {
                            'success': True,
                            'message': f"✅ Дата подписки для {username} обновлена",
                            'action': 'updated',
                            'old_expire': panel_2_expire,
                            'new_expire': panel_1_expire
                        }
                    else:
                        return {
                            'success': False,
                            'message': f"❌ Ошибка обновления подписки для {username}",
                            'action': 'error'
                        }
                else:
                    return {
                        'success': True,
                        'message': f"🔍 [ПРЕДПРОСМОТР] Будет обновлена подписка для {username}",
                        'action': 'would_update',
                        'old_expire': panel_2_expire,
                        'new_expire': panel_1_expire
                    }
            else:
                return {
                    'success': True,
                    'message': f"✅ Пользователь {username} уже синхронизирован",
                    'action': 'already_synced'
                }


async def sync_panels(dry_run: bool = False):
    """Основная функция синхронизации"""
    try:
        async with PanelSynchronizer() as sync:
            stats = await sync.full_sync(dry_run=dry_run)
            
            # Выводим итоговую статистику
            mode_text = "ПРЕДПРОСМОТР" if dry_run else "ВЫПОЛНЕНО"
            logger.info(f"""
🎯 === РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ ({mode_text}) ===
➕ Создано пользователей: {stats['users_created']}/{stats['users_to_create']}
🔄 Обновлено пользователей: {stats['users_updated']}/{stats['users_to_update']}
🗑️ Удалено пользователей: {stats['users_deleted']}/{stats['users_to_delete']}
❌ Ошибок: {stats['errors']}
📊 Всего операций: {len(stats['actions'])}
=======================================
""")
            
            if dry_run and stats['actions']:
                logger.info("📋 Запланированные действия:")
                for action in stats['actions'][:10]:  # Показываем первые 10
                    if action['type'] == 'create':
                        logger.info(f"   ➕ Создать: {action['username']} (до {action['expire_readable']})")
                    elif action['type'] == 'update':
                        logger.info(f"   🔄 Обновить: {action['username']} ({action['old_expire_readable']} → {action['new_expire_readable']})")
                    elif action['type'] == 'delete':
                        logger.info(f"   🗑️ Удалить: {action['username']}")
                
                if len(stats['actions']) > 10:
                    logger.info(f"   ... и еще {len(stats['actions']) - 10} действий")
            
            return stats
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка синхронизации: {e}")
        raise


async def sync_single_user(username: str, dry_run: bool = False):
    """Синхронизация одного пользователя"""
    try:
        async with PanelSynchronizer() as sync:
            result = await sync.sync_user(username, dry_run=dry_run)
            logger.info(result['message'])
            return result
            
    except Exception as e:
        logger.error(f"💥 Ошибка синхронизации пользователя {username}: {e}")
        raise


async def main():
    """Главная функция"""
    import sys

    print("🔄 Скрипт синхронизации панелей Marzban")
    print("📌 Панель 1 (основная) → Панель 2 (синхронизируемая)")
    print()

    # Проверяем флаги
    auto_yes = '--auto-yes' in sys.argv
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    # Убираем флаги из аргументов для получения имени пользователя
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--') and not arg.startswith('-')]

    if auto_yes:
        # Автоматический режим - полная синхронизация без подтверждения
        print("🤖 Автоматический режим (--auto-yes)")
        print("🚀 Запуск полной синхронизации...")
        print()
        await sync_panels(dry_run=False)
        
    elif len(args) > 0:
        # Синхронизация конкретного пользователя
        username = args[0]
        
        print(f"👤 Синхронизация пользователя: {username}")
        if dry_run:
            print("🔍 Режим предпросмотра")
        print()

        await sync_single_user(username, dry_run=dry_run)
        
    else:
        # Интерактивный режим
        print("🔧 Режимы запуска:")
        print("   1. Предпросмотр (без изменений)")
        print("   2. Полная синхронизация")
        print("   3. Отмена")
        print()

        while True:
            choice = input("Выберите режим (1/2/3): ").strip()

            if choice == '1':
                print("\n🔍 Запуск предпросмотра...")
                await sync_panels(dry_run=True)
                break
            elif choice == '2':
                print("\n⚠️ ВНИМАНИЕ! Это изменит данные во второй панели!")
                confirm = input("Продолжить? (yes/no): ").strip().lower()

                if confirm in ['yes', 'y', 'да']:
                    print("\n🚀 Запуск полной синхронизации...")
                    await sync_panels(dry_run=False)
                else:
                    print("❌ Синхронизация отменена")
                break
            elif choice == '3':
                print("❌ Отменено")
                break
            else:
                print("❌ Неверный выбор, попробуйте снова")

if __name__ == "__main__":
    asyncio.run(main())
