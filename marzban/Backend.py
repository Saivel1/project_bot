from types import NoneType
import aiohttp
import asyncio
import json
import logging
from config_data.config import load_config_marz, load_config_marz_dig, load_config_marz_mob

config = load_config_marz('.env')
MARZBAN_API_URL = config.url
MARZBAN_USER = config.login
MARZBAN_PASSWORD = config.password

config_dig = load_config_marz_dig('.env')
MARZBAN_API_URL_DIGITAL = config_dig.url
MARZBAN_USER_DIGITAL = config_dig.login
MARZBAN_PASSWORD_DIGITAL = config_dig.password

config_moba = load_config_marz_mob('.env')
MARZBAN_API_URL_MOBA = config_moba.url
MARZBAN_USER_MOBA = config_moba.login
MARZBAN_PASSWORD_MOBA = config_moba.password


logger = logging.getLogger(__name__)
format='[%(asctime)s] #%(levelname)-15s %(filename)s: %(lineno)d - %(pathname)s - %(message)s'
logging.basicConfig(level=logging.WARNING, format=format)


class MarzbanBackendContext:
    def __init__(self):
        self.session = None
        self.headers = {"accept": "application/json"}
        self.base_url = MARZBAN_API_URL

    async def __aenter__(self):
        """Вход в контекстный менеджер"""
        self.session = aiohttp.ClientSession()

        if not self.headers.get("Authorization"):
            await self.authorize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        await self._cleanup_session()

    async def authorize(self) -> None:
        data = {
            "username": MARZBAN_USER,
            "password": MARZBAN_PASSWORD,
        }

        async with self.session.post(f"{self.base_url}/api/admin/token", data=data) as response: # type: ignore
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                self.headers["Authorization"] = f"Bearer {token}"
            else:
                logger.warning(f"Ошибка авторизации: {response.status}")

    async def _cleanup_session(self):
        """Правильное закрытие сессии"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                # Даем время на закрытие соединений
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"Ошибка при закрытии сессии: {e}")
            finally:
                self.session = None
                self._authorized = False
                logger.debug(f"Сессия закрыта")

    async def create_user(self, username: str) -> dict:
        data = {
            "username": username,
            "proxies": {"vless": {"flow": "xtls-rprx-vision"}},
            "inbounds": {"vless": ["VLESS TCP REALITY"]},
        }

        async with self.session.post(f"{self.base_url}/api/user/", # type: ignore
                                   headers=self.headers, json=data) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                logger.warning(f"Ошибка создания пользователя: {response.status}")
        return None # type: ignore

    async def get_user(self, username: str) -> dict:

        async with self.session.get(f"{self.base_url}/api/user/{username}", # type: ignore
                                   headers=self.headers) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                logger.warning(f"Ошибка получения пользователя: {response.status}")
        return False # type: ignore

    async def get_users(self) -> dict:

        async with self.session.get(f"{self.base_url}/api/users/", # type: ignore
                                   headers=self.headers) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                logger.warning(f"Ошибка получения пользователей: {response.status}")
        return None # type: ignore

    async def delete_user(self, username: str) -> dict:

        async with self.session.delete(f"{self.base_url}/api/user/{username}", # type: ignore
                                   headers=self.headers) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                logger.warning(f"Ошибка удаления пользователя: {response.status}")
        return None # type: ignore

    async def set_inactive(self, username: str) -> dict:

        data = {
            'expire': 1750811597
        }

        async with self.session.put(f"{self.base_url}/api/user/{username}", # type: ignore
                                   headers=self.headers, json=data) as response:
            if response.status in (200, 201):
                return await response.json()
        return None # type: ignore

    async def modify_user(self, username: str, data: dict) -> dict:
        async with self.session.put(f"{self.base_url}/api/user/{username}", # type: ignore
                                   headers=self.headers, json=data) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                logger.warning(f"Ошибка изменения пользователя: {response.status}")
        return None # type: ignore


class MarzbanDigital(MarzbanBackendContext):
    def __init__(self):
        super().__init__()
        self.base_url = MARZBAN_API_URL_DIGITAL

    async def authorize(self) -> None:
        data = {
            "username": MARZBAN_USER_DIGITAL,
            "password": MARZBAN_PASSWORD_DIGITAL,
        }

        async with self.session.post(f"{self.base_url}/api/admin/token", data=data) as response: # type: ignore
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                self.headers["Authorization"] = f"Bearer {token}"
            else:
                logger.warning(f"Ошибка авторизации: {response.status}")


class MarzbanMoba(MarzbanBackendContext):
    def __init__(self):
        super().__init__()
        self.base_url = MARZBAN_API_URL_MOBA

    async def authorize(self) -> None:
        data = {
            "username": MARZBAN_USER_MOBA,
            "password": MARZBAN_PASSWORD_MOBA,
        }

        async with self.session.post(f"{self.base_url}/api/admin/token", data=data) as response: # type: ignore
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                self.headers["Authorization"] = f"Bearer {token}"
            else:
                logger.warning(f"Ошибка авторизации: {response.status}")
