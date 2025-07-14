from os import link
import logging
from keyboards import personal_acc as per_acc
from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message
from dataclasses import dataclass, asdict
from typing import Optional
from status.status_keys import get_message_by_status
from datetime import datetime
from marzban.Backend import MarzbanBackendContext
from refferal.refferal_logic import generate_refferal_code
from db.db_inject import db_manager as db
from db.db_model import User
from aiogram.types import LabeledPrice
from config_data.config import load_config
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, PreCheckoutQuery
from redis_bot.redis_main import RedisUserCache, get_user_cache_from_redis, update_redis_user_cache_field, UserCache
from aiogram.filters import CommandStart, CommandObject, Command
from typing import Dict, Any
import time
from keyboards.vpn_keyboards import VPNInstallKeyboards
from status.admin_midll import AdminMiddleware
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)
format='[%(asctime)s] #%(levelname)-15s %(filename)s: %(lineno)d - %(pathname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format)

#####################################
# Константы и конфигурация
#####################################
DAYS_PER_REFERRAL = 7
TRIAL_DAYS = 30

redis_cache = RedisUserCache()

# Загружаем конфиг в переменную
config = load_config('.env')
bot_token = config.tg_bot.token
BOT_TOKEN = bot_token
ADMIN_IDS = [482410857]

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
router = Router()
admin_router = Router()

#####################################
# Вспомогательные функции
#####################################
admin_router.message.middleware(AdminMiddleware(ADMIN_IDS))
admin_router.callback_query.middleware(AdminMiddleware(ADMIN_IDS))


# ==============================
# Админ команды
# ==============================

class AdminBalanceStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_balance = State()

@admin_router.message(Command("add_balance"))
async def start_add_balance(message: Message, state: FSMContext):
    """Начать процесс начисления баланса"""
    await state.set_state(AdminBalanceStates.waiting_for_user_id)
    await message.answer("""💳 Начисление баланса пользователю

📝 Отправьте ID пользователя:
Пример: 123456789

❌ Для отмены напишите /cancel""")

@admin_router.message(AdminBalanceStates.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
    """Обработка ID пользователя"""
    try:
        # Проверяем, что введен корректный ID
        user_id = int(message.text.strip())

        # Проверяем существование пользователя в БД
        user_data = await db.get_user(user_id)

        if not user_data:
            await message.answer(f"❌ Пользователь с ID {user_id} не найден в базе данных.")
            await state.clear()
            return

        # Сохраняем ID в состояние
        await state.update_data(target_user_id=user_id)
        await state.set_state(AdminBalanceStates.waiting_for_balance)

        # Показываем информацию о пользователе
        current_balance = user_data.balance or 0
        sub_end = user_data.subscription_end
        current_date = int(datetime.timestamp(datetime.now()))

        if sub_end and sub_end > current_date:
            days_left = (sub_end - current_date) // 86400
            status = f"✅ Активна ({days_left} дн.)"
        else:
            status = "❌ Неактивна"

        await message.answer(f"""👤 Пользователь найден!

🆔 ID: {user_id}
💰 Текущий баланс: {current_balance} ₽
📅 Подписка: {status}

💳 Введите сумму для начисления (в рублях):
Пример: 100

❌ Для отмены напишите /cancel""")

    except ValueError:
        await message.answer("❌ Некорректный ID пользователя. Введите только числа.")
    except Exception as e:
        logging.error(f"Ошибка при проверке пользователя: {e}")
        await message.answer("❌ Ошибка при проверке пользователя. Попробуйте позже.")
        await state.clear()

@admin_router.message(AdminBalanceStates.waiting_for_balance)
async def process_balance_amount(message: Message, state: FSMContext, redis_cache: RedisUserCache):
    """Обработка суммы для начисления"""
    try:
        # Получаем сумму
        balance_amount = int(message.text.strip())

        if balance_amount <= 0:
            await message.answer("❌ Сумма должна быть положительной. Введите корректную сумму:")
            return

        # Получаем данные из состояния
        state_data = await state.get_data()
        target_user_id = state_data['target_user_id']

        await message.answer("💸 Начисляем баланс...")

        # Получаем актуальные данные пользователя
        user_data = await db.get_user(target_user_id)
        if not user_data:
            await message.answer("❌ Пользователь больше не найден в базе данных.")
            await state.clear()
            return

        # Вычисляем новый баланс
        old_balance = user_data.balance or 0
        new_balance = old_balance + balance_amount

        # Вычисляем продление подписки (1 руб = 1 день в нашем примере)
        # Или используйте свою логику расчета дней
        days_to_add = balance_amount // 50 * 30 # Можете изменить формулу
        days_to_add = int(days_to_add)

        current_date = int(datetime.timestamp(datetime.now()))

        # Определяем новую дату окончания подписки
        if user_data.subscription_end and user_data.subscription_end > current_date:
            # Если подписка активна - добавляем к текущей дате окончания
            new_subscription_end = user_data.subscription_end + (days_to_add * 86400)
        else:
            # Если подписка неактивна - добавляем к текущей дате
            new_subscription_end = current_date + (days_to_add * 86400)

        # Операция с Marzban
        new_link, marzban_success = await safe_marzban_operation(
            str(target_user_id),
            {'expire': new_subscription_end},
            "admin_balance_addition"
        )

        if not marzban_success:
            await message.answer("❌ Ошибка обновления в системе VPN. Баланс не начислен.")
            await state.clear()
            return

        # Обновляем БД
        updated_user = await update_db(
            user_data,
            balance=new_balance,
            subscription_end=new_subscription_end,
            link=new_link if new_link else user_data.link
        )

        # Обновляем кэш
        await update_cache_fix(redis_cache, target_user_id, updated_user)

        # Логируем действие админа
        admin_id = message.from_user.id
        admin_username = message.from_user.username or "Unknown"
        logging.info(f"Админ {admin_id} (@{admin_username}) начислил {balance_amount}₽ пользователю {target_user_id}")

        # Уведомление о успехе
        days_added = days_to_add
        new_end_date = datetime.fromtimestamp(new_subscription_end).strftime('%d.%m.%Y %H:%M')

        success_text = f"""✅ Баланс успешно начислен!

👤 Пользователь: {target_user_id}
💰 Начислено: +{balance_amount} ₽
💳 Новый баланс: {new_balance} ₽
📅 Добавлено дней: +{days_added}
⏰ Подписка до: {new_end_date}

📝 Операция выполнена администратором {admin_username}"""

        await message.answer(success_text)

        # Опционально: уведомить пользователя
        try:
            await bot.send_message(
                target_user_id,
                f"""🎉 Вам начислен баланс!

💰 Начислено: +{balance_amount} ₽
📅 Подписка продлена на {days_added} дней
⏰ Действует до: {new_end_date}

Спасибо за использование нашего сервиса! 🔥"""
            )
        except Exception as e:
            logging.warning(f"Не удалось уведомить пользователя {target_user_id}: {e}")
            await message.answer("ℹ️ Пользователь не получил уведомление (заблокировал бота)")

        await state.clear()

    except ValueError:
        await message.answer("❌ Некорректная сумма. Введите только числа:")
    except Exception as e:
        logging.error(f"Ошибка начисления баланса: {e}")
        await message.answer("❌ Ошибка при начислении баланса. Попробуйте позже.")
        await state.clear()

@admin_router.message(Command("cancel"))
async def cancel_admin_operation(message: Message, state: FSMContext):
    """Отмена админской операции"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Операция отменена.")
    else:
        await message.answer("ℹ️ Нет активных операций для отмены.")

# Дополнительная команда для быстрого начисления в одну строку
@admin_router.message(Command("quick_balance"))
async def quick_add_balance(message: Message, redis_cache: RedisUserCache):
    """Быстрое начисление баланса: /quick_balance USER_ID AMOUNT"""
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("""❌ Неверный формат команды!

Использование: /quick_balance USER_ID AMOUNT

Пример: /quick_balance 123456789 100""")
            return

        user_id = int(args[1])
        balance_amount = int(args[2])

        if balance_amount <= 0:
            await message.answer("❌ Сумма должна быть положительной.")
            return

        # Проверяем пользователя
        user_data = await db.get_user(user_id)
        if not user_data:
            await message.answer(f"❌ Пользователь {user_id} не найден.")
            return

        await message.answer("💸 Начисляем баланс...")

        # Тот же код начисления что и выше...
        old_balance = user_data.balance or 0
        new_balance = old_balance + balance_amount
        days_to_add = balance_amount

        current_date = int(datetime.timestamp(datetime.now()))
        if user_data.subscription_end and user_data.subscription_end > current_date:
            new_subscription_end = user_data.subscription_end + (days_to_add * 86400)
        else:
            new_subscription_end = current_date + (days_to_add * 86400)

        new_link, marzban_success = await safe_marzban_operation(
            str(user_id),
            {'expire': new_subscription_end},
            "admin_quick_balance"
        )

        if not marzban_success:
            await message.answer("❌ Ошибка обновления в системе VPN.")
            return

        updated_user = await update_db(
            user_data,
            balance=new_balance,
            subscription_end=new_subscription_end,
            link=new_link if new_link else user_data.link
        )

        await update_cache_fix(redis_cache, user_id, updated_user)

        await message.answer(f"✅ Начислено {balance_amount}₽ пользователю {user_id}. Подписка продлена на {days_to_add} дней.")

    except ValueError:
        await message.answer("❌ Некорректные данные. Проверьте формат команды.")
    except Exception as e:
        logging.error(f"Ошибка быстрого начисления: {e}")
        await message.answer("❌ Ошибка операции.")

# ==============================
# Админ команды
# ==============================

#================================
# Платформа
#================================

# Платформы для установки
PLATFORM = ['android', 'ios', 'windows']

# Инструкции для платформ
PLATFORM_INSTRUCTIONS = {
    'android': """🤖 Инструкция для Android:

📱 Шаг 1: [Скачайте приложение](https://telegra.ph/Instrukciya-dlya-Android-03-07-2)

🔑 Шаг 2: Активация
• Откройте приложение
• Скопируйте ваш ключ доступа (В самом низу)
• Вставьте ключ в приложение
(Вставить из буфера обмена или В правом верхнем углу кнопка '+' > Вставить из буфера обмена)

⚡ Шаг 3: Подключение
• Нажмите большую кнопку или Треугольник справа снизу
• Разрешите создание VPN-подключения
• Дождитесь подключения (3-5 секунд)

✅ Готово! VPN активирован и защищает ваше соединение.

❓ Возникли проблемы? Нажмите "Помощь" ниже.""",
    'ios': """🍎 Инструкция для iOS/MacOS:

📱 Шаг 1: [Скачайте приложение](https://telegra.ph/Instrukciya-dlya-MacOS--IOS-03-07)

🔑 Шаг 2: Активация
• Откройте приложение
• Скопируйте ваш ключ доступа (В самом низу)
• Вставьте ключ в приложение
(Вставить из буфера обмена или В правом верхнем углу кнопка '+' > Вставить из буфера обмена)

⚙️ Шаг 3: Настройка
• Разрешите добавить VPN-конфигурацию
• Введите пароль/Touch ID/Face ID
• Подтвердите установку профиля

⚡ Шаг 4: Подключение
• Нажмите большую кнопку или Треугольник справа снизу
• Нажмите "Подключиться"
• Дождитесь подключения (3-5 секунд)

✅ Готово! VPN активирован. В статус-баре появится значок VPN.

❓ Возникли проблемы? Нажмите "Помощь" ниже.""",
    'windows': """💻 Инструкция для Windows:

💻 Шаг 1: [Скачайте приложение](https://telegra.ph/Instrukciya-dlya-Windows-03-07-3)

📥 Шаг 2: Установка
• Следуйте инструкциям установщика
• Выберите папку для установки
• Дождитесь завершения установки
• Запустите приложение

🔑 Шаг 2: Активация
• Откройте приложение
• Скопируйте ваш ключ доступа (В самом низу)
• Вставьте ключ в приложение
(Правой кнопкой мыши в свободном поле 'Вставить из буфера обмена' или в Happ сразу вставить ключ)

⚡ Шаг 4: Подключение
• Нажмите кнопку "Подключиться"
• При первом запуске разрешите изменения
• Дождитесь подключения (3-5 секунд)

✅ Готово! VPN активирован. В трее появится иконка приложения.

❓ Возникли проблемы? Нажмите "Помощь" ниже."""
}

def get_platform_message(platform: str) -> dict:
    """Возвращает инструкцию для конкретной платформы"""
    return {
        'text': PLATFORM_INSTRUCTIONS.get(platform, '❌ Платформа не найдена'),
        'keyboard': VPNInstallKeyboards.platform_chosen()
    }




#================================
# Окончание
#================================

async def update_cache_fix(redis_cache: RedisUserCache, user_id: int, data: Dict[str, Any], **kwargs):
   """Обновляет кэш пользователя с данными из БД и дополнительными параметрами"""
   default_data = UserCache(
       user_id=user_id,
       balance=data.balance,
       trial=data.trial,
       link=data.link,
       subscription_end=data.subscription_end,
       trial_end=data.trial_end,
       referral_count=data.referral_count
   )
   current_data = asdict(default_data)
   current_data.update(kwargs)
   output = await update_redis_user_cache_field(redis_cache, **current_data)
   return output

async def update_db(data: Dict[str, Any], **kwargs):
   """Обновляет пользователя в БД"""
   try:
       current = data
       current_dict = asdict(current)
       current_dict.update(kwargs)
       update_data = User(**current_dict)
       await db.update_user(update_data)
       logging.info(f"БД обновлена для пользователя {current_dict.get('user_id')}: {kwargs}")
       return update_data
   except Exception as e:
       logging.error(f"Ошибка обновления БД для пользователя {current_dict.get('user_id', 'unknown')}: {e}")
       raise

async def always_cache(redis_cache: RedisUserCache, user_id: int, username: str):
   """Получает данные пользователя из кэша или создает кэш из БД"""
   start_time = time.time()
   try:
       user_cache = await get_user_cache_from_redis(redis_cache, user_id)
       if user_cache:
           user_data = user_cache
           logging.info(f"Пользователь {user_id} получен из кэша за {time.time() - start_time:.3f}с")
       else:
           data_db = await db.get_user(user_id)
           if not data_db:
               data_db = await db.get_or_create_user(user_id, username)
               logging.info(f"Создан новый пользователь {user_id}")
           user_data = await update_cache_fix(redis_cache, user_id, data_db)
           logging.info(f"Пользователь {user_id} кэширован из БД за {time.time() - start_time:.3f}с")
       return user_data
   except Exception as e:
       logging.error(f"Ошибка получения данных пользователя {user_id}: {e}")
       raise

async def safe_marzban_operation(user_id_str: str, operation_data: dict, operation_name: str):
   """Безопасное выполнение операции с Marzban"""
   try:
       async with MarzbanBackendContext() as backend:
           res = await backend.get_user(user_id_str)
           if res:
               new_link = res['subscription_url']
               await backend.modify_user(user_id_str, operation_data)
           else:
               res = await backend.create_user(user_id_str)
               new_link = res['subscription_url']
               await backend.modify_user(user_id_str, operation_data)

           logging.info(f"Marzban операция '{operation_name}' успешна для пользователя {user_id_str}")
           return new_link, True
   except Exception as e:
       logging.error(f"Ошибка Marzban операции '{operation_name}' для пользователя {user_id_str}: {e}")
       return None, False

async def process_referral_bonus(user_id: int):
   """Обрабатывает реферальный бонус - помечает пользователя как eligible"""
   try:
       success = await db.update_referral_bonus(user_id)
       if success:
           logging.info(f"Пользователь {user_id} помечен как eligible для реферальных бонусов")
       return success
   except Exception as e:
       logging.error(f"Ошибка обработки реферального бонуса для пользователя {user_id}: {e}")
       return False

def validate_positive_int(value: int, name: str) -> bool:
   """Валидация положительного числа"""
   if not isinstance(value, int) or value <= 0:
       logging.warning(f"Некорректное значение {name}: {value}")
       return False
   return True

#####################################
# Основные функции
#####################################

def create_personal_acc_text(balance: int = 0, subscription_end: int = 0) -> str:
   current_date = int(datetime.timestamp(datetime.now()))
   balance_text = balance if balance else 0
   if current_date > subscription_end:
       sub_text = 0
       hours = 0
   else:
       sub_text = (subscription_end - current_date)//86400 if subscription_end else 0
       hours = ((subscription_end - current_date)//3600 - sub_text * 24) if subscription_end else 0
   return f"""
📊 Личный кабинет

💰 Потрачено в сервисе: {balance_text} ₽
📈 Дней подписки: {int(sub_text)} | Часов: {int(hours)}
   """.strip()

def help_message(amount: int):
   keyboard = InlineKeyboardMarkup(inline_keyboard=[
       [InlineKeyboardButton(text=f"Оплатить {amount} ⭐", pay=True)],
       [InlineKeyboardButton(text="Главное меню", callback_data="start_menu_in_payment")]
   ])
   return keyboard

#####################################
# Хэндлеры
#####################################

@router.callback_query(F.data == 'trial_per')
async def trial_per(callback: CallbackQuery, redis_cache: RedisUserCache):
   current_date = int(datetime.timestamp(datetime.now()))
   user_id = callback.from_user.id

   await callback.message.edit_text(
       text="Активация пробного периода...",
       reply_markup=None
   )

   try:
       data_db = await db.get_user(user_id)
       if not data_db:
           raise ValueError(f"Пользователь {user_id} не найден в БД")

       if current_date > data_db.subscription_end:
           new_date = current_date + (TRIAL_DAYS * 86400)
       else:
           new_date = data_db.subscription_end + (TRIAL_DAYS * 86400)

       if not validate_positive_int(new_date, "trial_end_date"):
           raise ValueError("Некорректная дата окончания пробного периода")

       # Операция с Marzban
       new_link, marzban_success = await safe_marzban_operation(
           str(user_id),
           {'expire': new_date},
           "trial_activation"
       )

       if not marzban_success:
           await callback.message.edit_text(
               text="❌ Ошибка активации в системе. Попробуйте позже.",
               reply_markup=None
           )
           return

       # Обновляем БД
       data_db = await update_db(
           data_db,
           subscription_end=new_date,
           link=new_link,
           trial='in_progress',
           trial_end=new_date
       )

       # Обновляем кэш
       user_data = await update_cache_fix(redis_cache, user_id, data_db)

       # Обрабатываем реферальный бонус (только новая логика БД)
       await process_referral_bonus(user_id)

       # Логгирование
       await db.log_user_action(user_id, callback.data)

       message = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end, user_data.balance)
       await callback.message.edit_text(
           text=message['text'],
           reply_markup=message['keyboard']
       )

   except Exception as e:
       logging.error(f"Ошибка активации пробного периода для пользователя {user_id}: {e}")
       await callback.message.edit_text(
           text="❌ Произошла ошибка при активации пробного периода. Обратитесь в поддержку.",
           reply_markup=None
       )

@router.callback_query(F.data == 'personal_acc')
async def personal_acc(callback: CallbackQuery, redis_cache: RedisUserCache):
   current_date = int(datetime.timestamp(datetime.now()))
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)

       # Считаем неиспользованных рефералов
       cnt = await db.count_unused_referrals(user_id)
       out = cnt if cnt else 'Пока никого'

       await callback.message.edit_text(
           text=f'Загружаем личный кабинет... \n\n\n Количество рефералов: {out}',
           reply_markup=None
       )

       if cnt and (user_data.balance or user_data.trial != 'never_used'):
           # Вычисляем новую дату подписки
           if user_data.subscription_end > current_date:
               modified_data = user_data.subscription_end
           else:
               modified_data = current_date

           modified_data += 86400 * DAYS_PER_REFERRAL * cnt

           if not validate_positive_int(modified_data, "referral_bonus_date"):
               logging.error(f"Некорректная дата бонуса рефералов для пользователя {user_id}")
           else:
               # Операция с Marzban
               new_link, marzban_success = await safe_marzban_operation(
                   str(user_id),
                   {'expire': modified_data},
                   "referral_bonus"
               )

               if marzban_success:
                   # Обновляем БД
                   data_db = await db.get_user(user_id)
                   await update_db(data_db, subscription_end=modified_data)

                   # Обновляем кэш
                   user_data = await update_cache_fix(
                       redis_cache,
                       user_id,
                       user_data,
                       subscription_end=modified_data
                   )

                   # Помечаем рефералов как использованных ТОЛЬКО после успеха
                   marked_count = await db.mark_referrals_as_used(user_id)
                   if marked_count != cnt:
                       logging.warning(f"Несоответствие рефералов для пользователя {user_id}: считали {cnt}, пометили {marked_count}")
               else:
                   logging.error(f"Не удалось начислить реферальный бонус пользователю {user_id} - Marzban недоступен")

       text_message = create_personal_acc_text(user_data.balance, user_data.subscription_end)
       link = user_data.link if user_data.link and (user_data.trial != 'never_used' or user_data.subscription_end) else "Пока пусто."

       if user_data.trial == 'never_used':
           keyboard = per_acc.VPNPersAccKeyboards.personal_acc_new()
       else:
           keyboard = per_acc.VPNPersAccKeyboards.personal_acc()

       await db.log_user_action(user_id, callback.data)

       await callback.message.edit_text(
           text=f'{text_message} \n\n 🔗 Ссылка на подписку: **`{link}`**',
           reply_markup=keyboard,
           parse_mode='Markdown'
       )

   except Exception as e:
       logging.error(f"Ошибка в личном кабинете для пользователя {user_id}: {e}")
       await callback.message.edit_text(
           text="❌ Ошибка загрузки личного кабинета. Попробуйте позже.",
           reply_markup=None
       )

@router.callback_query(F.data == 'start_menu_in_payment')
async def start_menu_in_payment(callback: CallbackQuery, redis_cache: RedisUserCache):
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)
       message = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end, user_data.balance)

       await callback.message.delete()
       await callback.message.answer(
           text=message['text'],
           reply_markup=message['keyboard']
       )
   except Exception as e:
       logging.error(f"Ошибка возврата в главное меню для пользователя {user_id}: {e}")

@router.callback_query(F.data.in_(["to_pay_year", "to_pay_6_months", "to_pay_3_months", "to_pay_month", "to_pay_best"]))
async def handler_payment_success(callback: CallbackQuery, redis_cache: RedisUserCache):
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)

       plan = {
           "to_pay_year": 360,
           "to_pay_6_months": 180,
           "to_pay_3_months": 90,
           "to_pay_month": 30,
           "to_pay_best": 100
       }

       if callback.data not in plan:
           logging.error(f"Неизвестный план платежа: {callback.data}")
           return

       # Помечаем пользователя как eligible для реферальных бонусов
       await process_referral_bonus(user_id)

       await db.log_user_action(user_id, callback.data)
       await callback.message.delete()

       # Проверяем доступность Marzban перед созданием инвойса
       _, marzban_available = await safe_marzban_operation(
           str(user_id),
           {},  # Пустая операция для проверки
           "connection_check"
       )

       cnt = plan[callback.data]
       if callback.data == 'to_pay_best':
           monthes = 120
       else:
           monthes = plan[callback.data]

       if marzban_available:
           prices = [LabeledPrice(label="Оплата", amount=cnt)]
           await callback.message.answer_invoice(
               title=f"💫 Подписка на {monthes // 30} мес.",
               description=f'Для оформления подписки необходимо произвести оплату.',
               payload=callback.data,
               currency="XTR",
               prices=prices,
               start_parameter="premium_payment",
               reply_markup=help_message(cnt)
           )
       else:
           message = get_message_by_status("payment_unsuccess", user_data.trial, user_data.subscription_end, user_data.balance)
           await callback.message.answer(
               text=f"{message['text']}\n\n❌ Сервис временно недоступен. Попробуйте позже.",
               reply_markup=message['keyboard']
           )

   except Exception as e:
       logging.error(f"Ошибка создания платежа для пользователя {user_id}: {e}")

@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout: PreCheckoutQuery, bot: Bot):
   await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, redis_cache: RedisUserCache):
   payment = message.successful_payment
   user_id = message.from_user.id
   charge_id = payment.telegram_payment_charge_id
   invoice = payment.invoice_payload
   username = message.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)
       current_date = int(datetime.timestamp(datetime.now()))

       plan = {
           "to_pay_year": 600,
           "to_pay_6_months": 300,
           "to_pay_3_months": 150,
           "to_pay_month": 50,
           "to_pay_best": 180
       }

       if invoice not in plan:
           logging.error(f"Неизвестный план в платеже: {invoice}")
           await message.answer("❌ Ошибка обработки платежа. Обратитесь в поддержку.")
           return

       amount = plan[invoice]

       if invoice == "to_pay_best":
           amount_time = 200
       else:
           amount_time = plan[invoice]

       # Логируем платеж
       await db.create_payment(user_id, amount, "success", charge_id)

       # Помечаем пользователя как eligible для реферальных бонусов
       await process_referral_bonus(user_id)

       new_balance = user_data.balance + amount

       if current_date > user_data.subscription_end:
           new_date = current_date + (amount_time * 86400 * 30) // 50
            # Для теста поставим пол дня или несколько часов
           #new_date = current_date + (amount * 3600 * 6) // 50
       else:
           new_date = user_data.subscription_end + (amount_time * 86400 * 30) // 50
           #new_date = user_data.subscription_end + (amount * 3600 * 6) // 50

       if not validate_positive_int(new_date, "subscription_end_date"):
           raise ValueError("Некорректная дата окончания подписки")

       # Операция с Marzban
       new_link, marzban_success = await safe_marzban_operation(
           str(user_id),
           {'expire': new_date},
           "payment_processing"
       )

       if not marzban_success:
           await message.answer("❌ Платеж получен, но произошла ошибка активации. Обратитесь в поддержку.")
           return

       # Обновляем кэш
       user_data = await update_cache_fix(
           redis_cache,
           user_id,
           user_data,
           balance=new_balance,
           subscription_end=new_date,
           link=new_link
       )

       # Обновляем БД
       data_db = await db.get_user(user_id)
       await update_db(data_db, balance=new_balance, subscription_end=new_date, link=new_link)

       messages = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end, user_data.balance)

       await message.answer(
           text=messages['text'],
           reply_markup=messages['keyboard']
       )

   except Exception as e:
       logging.error(f"Ошибка обработки платежа для пользователя {user_id}: {e}")
       await message.answer("❌ Произошла ошибка при обработке платежа. Обратитесь в поддержку.")

@router.callback_query(F.data.in_(['buy_key', 'buy_key_in_install']))
async def buy_key(callback: CallbackQuery, redis_cache: RedisUserCache):
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)
       message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end, user_data.balance)

       await db.log_user_action(user_id, callback.data)

       await callback.message.edit_text(
           text=message['text'],
           reply_markup=message['keyboard']
       )
   except Exception as e:
       logging.error(f"Ошибка в buy_key для пользователя {user_id}: {e}")

@router.callback_query(F.data.in_(['invite_in_install', 'invite']))
async def invite_handler(callback: CallbackQuery, redis_cache: RedisUserCache):
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)
       message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end, user_data.balance)
       ref_link = generate_refferal_code(user_id)

       await db.log_user_action(user_id, callback.data)

       await callback.message.edit_text(
           text=f"{message['text']} \n\n\n {ref_link}",
           reply_markup=message['keyboard']
       )
   except Exception as e:
       logging.error(f"Ошибка в invite_handler для пользователя {user_id}: {e}")

@router.callback_query(F.data.in_(PLATFORM))
async def platform_handler(callback: CallbackQuery, redis_cache: RedisUserCache):
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)
       message = get_platform_message(callback.data)
       sub_link = user_data.link

       await db.log_user_action(user_id, callback.data)

       await callback.message.edit_text(
          text=f"{message['text']}\n\n🔗 Ссылка на подписку: **`{sub_link}`**",
          reply_markup=message['keyboard'],
          parse_mode='Markdown'
        )
   except Exception as e:
       logging.error(f"Ошибка в invite_handler для пользователя {user_id}: {e}")



@router.callback_query()
async def universal_handler(callback: CallbackQuery, redis_cache: RedisUserCache):
   user_id = callback.from_user.id
   username = callback.from_user.username

   try:
       user_data = await always_cache(redis_cache, user_id, username)
       current_date = int(datetime.timestamp(datetime.now()))

       # Проверяем истечение подписки
       if user_data.trial == 'in_progress' and current_date > user_data.subscription_end:
           data_db = await db.get_user(user_id)
           new_data = await update_db(data_db, trial='expired')
           user_data = await update_cache_fix(redis_cache, user_id, new_data)

       await db.log_user_action(user_id, callback.data)

       message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end, user_data.balance)
       await callback.message.edit_text(
           text=message['text'],
           reply_markup=message['keyboard'],
           parse_mode='Markdown'
       )
   except Exception as e:
       logging.error(f"Ошибка в universal_handler для пользователя {user_id}: {e}")

@router.message(CommandStart())
async def process_start_command(message: Message, command: CommandObject, redis_cache: RedisUserCache):
   ref_id = command.args
   user_id = message.from_user.id
   username = message.from_user.username

   try:
       user_cache = await get_user_cache_from_redis(redis_cache, user_id)
       if user_cache:
           user_data = user_cache
       else:
           data = await db.get_user(user_id)
           if not data:
               data = await db.get_or_create_user(user_id, username)
           user_data = await update_cache_fix(redis_cache, user_id, data)

           # Обработка первого визита и рефералов
           if not data.first_visit_completed:
               data = await update_db(data, first_visit_completed=True)

               if ref_id:
                   try:
                       ref_id_int = int(ref_id)
                       if ref_id_int == user_id:
                           logging.warning(f"Пользователь {user_id} пытался использовать свою же реферальную ссылку")
                       else:
                           referral_success = await db.create_referral(ref_id_int, user_id)
                           if referral_success:
                               logging.info(f"Создана реферальная связь: {ref_id_int} -> {user_id}")
                           else:
                               logging.warning(f"Не удалось создать реферальную связь: {ref_id_int} -> {user_id}")
                   except (ValueError, TypeError) as e:
                       logging.warning(f"Некорректный реферальный ID: {ref_id}, ошибка: {e}")

       message_text = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end)
       await db.log_user_action(user_id, "", message.text)

       await message.answer(
           text=message_text['text'],
           reply_markup=message_text['keyboard']
       )

   except Exception as e:
       logging.error(f"Ошибка в процессе старта для пользователя {user_id}: {e}")
       # Отправляем базовое сообщение даже при ошибке
       try:
           fallback_message = get_message_by_status('start_menu', 'never_used', 0)
           await message.answer(
               text=fallback_message['text'],
               reply_markup=fallback_message['keyboard']
           )
       except:
           await message.answer("Добро пожаловать! Произошла техническая ошибка, попробуйте позже.")

@router.message(Command('paybeck'))
async def process_paybeck_command(message: Message, bot: Bot, command: CommandObject):
   try:
       await bot.refund_star_payment(message.from_user.id, command.args)
   except Exception as e:
       logging.error(f"Ошибка возврата платежа: {e}")
       await message.answer("❌ Ошибка обработки возврата. Обратитесь в поддержку.")
