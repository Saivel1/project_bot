import asyncio
from yookassa import Payment, Configuration
import time
import uuid
import json
import logging
from config_data.config import load_yookassa_config

config = load_yookassa_config('.env')


logger = logging.getLogger(__name__)
format='[%(asctime)s] #%(levelname)-15s %(filename)s: %(lineno)d - %(pathname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format)

Configuration.account_id = config.account_id
Configuration.secret_key = config.secret_key


class PaymentYoo:
    def __init__(self):
        self.id = None
        self.link = None

    async def create_payment(self, amount: int, plan: str, email: str):
        payment_id = uuid.uuid4()
        try:
            payment = Payment.create({
                "amount": {
                    "value": amount,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/ivvpnbot"
                },
                "capture": True,
                "description": "Подписка на VPN. В боте @ivvpnbot",
                "receipt": {
                    "customer": {
                            "email": email # Обязательно для отправки чека
                        },
                        "items": [
                            {
                                "description": plan,
                                "quantity": 1.0,
                                "amount": {
                                    "value": amount,
                                    "currency": "RUB"
                                },
                                "vat_code": "2" # Код НДС, например "2" для "без НДС"
                            }
                        ]
                }
            }, payment_id)

            payment_data = json.loads(payment.json())

            self.id = payment_data['id']
            self.link = payment.confirmation.confirmation_url
        except Exception as e:
            logger.warning(f'Ошибка создания платежа: {e}')

        return None

    async def get_status(self, id: str):
        try:
            return Payment.find_one(id).status
        except Exception as e:
            logger.warning(f'Ошибка получения статуса платежа: {e}')
        return None

    async def check_if_succeed(self):
        start_time = time.time()
        duration = 600
        try:
            end_time = 0
            while end_time - start_time < duration:
                if await self.get_status(self.id) == "succeeded":
                    return "YES"
                end_time = time.time()
                await asyncio.sleep(5)
            return "NO"
        except Exception as e:
            logger.warning(f'Ошибка проверки статуса платежа: {e}')
        return None
