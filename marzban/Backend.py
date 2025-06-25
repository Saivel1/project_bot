from types import NoneType
import aiohttp
import asyncio
import json

#MARZBAN_API_URL = "https://ivvpn.digital"  # Замените на URL вашего Marzban API
#MARZBAN_USER = "admin"  # Замените на имя пользователя Marzban
#MARZBAN_PASSWORD = "aX8xH7pD9ugD"  # Замените на пароль пользователя Marzban

MARZBAN_API_URL = "https://bratva1234.duckdns.org:64526"  # Замените на URL вашего Marzban API
MARZBAN_USER = "iv"  # Замените на имя пользователя Marzban
MARZBAN_PASSWORD = "M7L7Snhagn"  # Замените на пароль пользователя Marzban

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
        if self.session:
            await self.session.close()

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
        return None # type: ignore

    async def get_user(self, username: str) -> dict:

        async with self.session.get(f"{self.base_url}/api/user/{username}", # type: ignore
                                   headers=self.headers) as response:
            if response.status in (200, 201):
                return await response.json()
        return False # type: ignore

    async def get_users(self) -> dict:

        async with self.session.get(f"{self.base_url}/api/users/", # type: ignore
                                   headers=self.headers) as response:
            if response.status in (200, 201):
                return await response.json()
        return None # type: ignore

    async def delete_user(self, username: str) -> dict:

        async with self.session.delete(f"{self.base_url}/api/user/{username}", # type: ignore
                                   headers=self.headers) as response:
            if response.status in (200, 201):
                return await response.json()
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


