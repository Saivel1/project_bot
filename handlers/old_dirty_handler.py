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
from refferal.refferal_logic import generate_refferal_code, ref_base
from refferal.refferal_handler import reward_add, reward_set, switch_to_used
from db.db_inject import db_manager as db
from db.db_model import User
from aiogram.types import LabeledPrice
from config_data.config import load_config
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, PreCheckoutQuery
from redis_bot.redis_main import RedisUserCache, get_user_cache_from_redis, update_redis_user_cache_field, UserCache
from aiogram.filters import CommandStart, CommandObject, Command
from typing import Dict, Any


logger = logging.getLogger(__name__)
format='[%(asctime)s] #%(levelname)-15s %(filename)s: %(lineno)d - %(pathname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format)

#####################################
# Тестируем редис
#####################################

redis_cache = RedisUserCache()

async def update_cache_fix(redis_cache: RedisUserCache, user_id: int, data: Dict[str, Any], **kwargs):
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

#####################################
# Тестируем редис
#####################################

# ==================================
# Тут тестируем DB
# ==================================

async def update_db(data: Dict[str, Any], **kwargs):
    current = data
    current_dict = asdict(current)
    current_dict.update(kwargs)
    update_data = User(**current_dict)
    await db.update_user(update_data)
    return update_data

# ==================================
# Тут кончик
# ==================================
async def always_cache(redis_cache: RedisUserCache, user_id, username):
    user_cache = await get_user_cache_from_redis(redis_cache, user_id)
    if user_cache:
        user_data = user_cache
    else:
        data_db = await db.get_user(user_id)
        if not data_db:
            data_db = await db.get_or_create_user(user_id, username)
        user_data = await update_cache_fix(redis_cache, user_id, data_db)
    return user_data

# Загружаем конфиг в переменную
config = load_config('.env')
bot_token = config.tg_bot.token
BOT_TOKEN = bot_token


# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
router = Router()


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

###########################################################
# Написать хэндлер для реакции на состояние пользователя. https://stepik.org/lesson/891577/step/5?unit=896427
###########################################################

@router.callback_query(F.data == 'trial_per')
async def trial_per(callback: CallbackQuery, redis_cache: RedisUserCache):
    current_date = datetime.timestamp(datetime.now())
    # Используем функцию для получения правильного сообщения
    # Будет увеличиваться на N дней, пока остаётся нетронутым.
    n_days = 30
    user_id = callback.from_user.id
    data_db = await db.get_user(user_id)

    if current_date > data_db.subscription_end:
        new_date = current_date + (n_days * 86400)
    else:
        new_date = data_db.subscription_end + (n_days * 86400)
    new_date = int(new_date)

    # Сообщение об активации
    await callback.message.edit_text(
        text="Активация пробного периода...",
        reply_markup=None
    )
    # Сначала отправляем в Марзбан
    async with MarzbanBackendContext() as backend:
        res = await backend.get_user(str(callback.from_user.id))
        data_to_modify = {'expire': new_date}
        if res:
            new_link = res['subscription_url']
        else:
            res = await backend.create_user(str(callback.from_user.id))
            new_link = res['subscription_url']
        sub_end = await backend.modify_user(str(callback.from_user.id), data_to_modify)

    data_db = await update_db(data_db, subscription_end=new_date, link=new_link, trial='in_progress', trial_end=new_date)
    # Обновляем кэш
    user_data = await update_cache_fix(redis_cache, user_id, data_db)
    # Переключаем в True при активации пробного периода
    await db.update_referral_bonus(user_id)
    #Логгирование дейсвтия.
    await db.log_user_action(callback.from_user.id, callback.data)
    message = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end, user_data.balance)

    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

@router.callback_query(F.data == 'personal_acc')
async def personal_acc(callback: CallbackQuery, redis_cache: RedisUserCache):
    current_date = int(datetime.timestamp(datetime.now()))
    user_id = callback.from_user.id
    username = callback.from_user.username

    user_data = await always_cache(redis_cache, user_id, username)

    # Сразу обнуляет число
    cnt = await db.count_unused_referrals(user_id)

    out = cnt if cnt else 'Пока никого'

    await callback.message.edit_text(
        text=f'Загружаем личный кабинет... \n\n\n Количество рефералов: {out}',
        reply_markup=None
    )
    data_db = await db.get_user(user_id)
    total_ref_cnt = cnt + user_data.referral_count

    if cnt and (user_data.balance or user_data.trial != 'never_used'):
        async with MarzbanBackendContext() as backend:
            res = await backend.get_user(str(user_id))
            modified_data = 0
            if res:
                if user_data.subscription_end > current_date:
                    modified_data = user_data.subscription_end
                else:
                    modified_data = current_date

                modified_data += 86400 * 7 * cnt
                modified_data = int(modified_data)
                data_to_modify = {'expire': modified_data}
                await backend.modify_user(str(user_id), data_to_modify)
                await update_db(data_db, subscription_end=modified_data)
                user_data = await update_cache_fix(redis_cache, user_id, user_data, subscription_end=modified_data)
                await db.mark_referrals_as_used(user_id)

    text_message = create_personal_acc_text(user_data.balance, user_data.subscription_end)
    link = user_data.link if user_data.link and (user_data.trial != 'never_used' or user_data.subscription_end) else "Пока пусто."

    if user_data.trial == 'never_used':
        keyboard = per_acc.VPNPersAccKeyboards.personal_acc_new()
    else:
        keyboard = per_acc.VPNPersAccKeyboards.personal_acc()
    # Логгирование действия
    await db.log_user_action(user_id, callback.data)

    await callback.message.edit_text(
        text=f'{text_message} \n\n Ссылка на подписку: {link}',
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'start_menu_in_payment')
async def start_menu_in_payment(callback: CallbackQuery, redis_cache: RedisUserCache):
    user_id = callback.from_user.id
    username = callback.from_user.username
    user_data = await always_cache(redis_cache, user_id, username)

    message = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end, user_data.balance)

    await callback.message.delete()

    await callback.message.answer(
        text=message['text'],
        reply_markup=message['keyboard']
    )

def help_message(amount: int):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Оплатить {amount} ⭐", pay=True)],
            [InlineKeyboardButton(text="Главное меню", callback_data="start_menu_in_payment")]
        ])
        return keyboard

@router.callback_query(F.data.in_(["to_pay_year", "to_pay_6_months", "to_pay_3_months", "to_pay_month"]))
async def handler_payment_success(callback: CallbackQuery, redis_cache: RedisUserCache):
    user_id = callback.from_user.id
    username = callback.from_user.username
    user_data = await always_cache(redis_cache, user_id, username)

    plan = {
        "to_pay_year": 360,
        "to_pay_6_months": 180,
        "to_pay_3_months": 90,
        "to_pay_month": 30
    }
    await reward_set(ref_base, callback.from_user.id)

    message = get_message_by_status("payment_unsuccess", user_data.trial, user_data.subscription_end, user_data.balance)

    # Логгирование дейсвтия
    await db.log_user_action(callback.from_user.id, callback.data)

    await callback.message.delete()

    try:
        async with MarzbanBackendContext() as backend:
            res = await backend.get_user(str(callback.from_user.id))
            prices = [LabeledPrice(label="Премиум подписка", amount=1)]

            await callback.message.answer_invoice(
                title=f"💫 Подписка на {plan[callback.data] // 30} месяцев.",
                description=f'Для оформления подписки необходимо оплатить сумму ниже.',
                payload=callback.data,
                currency="XTR",
                prices=prices,
                start_parameter="premium_payment",
                reply_markup=help_message(1)
            )
    except Exception as e:
        logging.error(f"Ошибка обработки платежа: {e}")
        await callback.message.answer(
            text=message['text'],
            reply_markup=message['keyboard']
        )


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, redis_cache: RedisUserCache):
    try:
        payment = message.successful_payment
        user_id = message.from_user.id
        charge_id = payment.telegram_payment_charge_id
        invoice = payment.invoice_payload
        username = message.from_user.username

        user_data = await always_cache(redis_cache, user_id, username)
        current_date = int(datetime.timestamp(datetime.now()))

        await db.update_referral_bonus(user_id)

        plan = {
        "to_pay_year": 600,
        "to_pay_6_months": 300,
        "to_pay_3_months": 150,
        "to_pay_month": 50
        }

        await db.create_payment(user_id, plan[invoice], "success", charge_id)

        new_balance = user_data.balance + plan[invoice]

        if current_date > user_data.subscription_end:
            new_date = current_date + (plan[invoice] * 86400 * 30)//50
        else:
            new_date = user_data.subscription_end + (plan[invoice] * 86400 * 30)//50

        user_id = str(message.from_user.id)
        async with MarzbanBackendContext() as backend:
            res = await backend.get_user(user_id)
            if res:
                data_to_modify = {'expire': new_date}
            else:
                data_to_modify = {'expire': new_date}
                res = await backend.create_user(user_id)
            new_link = res['subscription_url']

            sub_end = await backend.modify_user(user_id, data_to_modify)

        user_data = await update_cache_fix(redis_cache, int(user_id), user_data, balance=new_balance, subscription_end=new_date, link=new_link)
        data_db = await db.get_user(int(user_id))
        await update_db(user_data, balance=new_balance, subscription_end=new_date, link=new_link)

        messages = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end, user_data.balance)

        await message.answer(
            text=messages['text'],
            reply_markup=messages['keyboard']
        )

    except Exception as e:
        logging.error(f"Ошибка обработки платежа: {e}")
        await message.answer("❌ Произошла ошибка, обратитесь в поддержку")

@router.callback_query(F.data.in_(['buy_key', 'buy_key_in_install']))
async def buy_key(callback: CallbackQuery, redis_cache: RedisUserCache):
    user_id = callback.from_user.id
    username = callback.from_user.username
    user_data = await always_cache(redis_cache, user_id, username)

    message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end, user_data.balance)

    # Логгирование дейсвтия
    await db.log_user_action(callback.from_user.id, callback.data)

    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )


@router.callback_query(F.data.in_(['invite_in_install', 'invite']))
async def invite_handler(callback: CallbackQuery, redis_cache: RedisUserCache):
    user_id = callback.from_user.id
    username = callback.from_user.username
    user_data = await always_cache(redis_cache, user_id, username)

    message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end, user_data.balance)
    ref_link = generate_refferal_code(user_id)

    # Логгирование дейсвтия
    await db.log_user_action(callback.from_user.id, callback.data)

    await callback.message.edit_text(
        text=f"{message['text']} \n\n\n {ref_link}",
        reply_markup=message['keyboard']
    )

# ==========================================
# Универсальный хэндлер с условиями
# ==========================================

@router.callback_query()
async def universal_handler(callback: CallbackQuery, redis_cache: RedisUserCache):
    user_id = callback.from_user.id
    username = callback.from_user.username
    user_data = await always_cache(redis_cache, user_id, username)
    current_date = int(datetime.timestamp(datetime.now()))

    if user_data.trial == 'in_progress' and current_date > user_data.subscription_end:
        data_db = await db.get_user(user_id)
        new_data = await update_db(data_db, trial='expired')
        await update_cache_fix(redis_cache, user_id, new_data)

    # Логгирование дейсвтия
    await db.log_user_action(user_id, callback.data)
    # Используем функцию для получения сообщения по статусу
    message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end, user_data.balance)
    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

########################################
# Старт
########################################

@router.message(CommandStart())
async def process_start_command(message: Message, command: CommandObject,  redis_cache: RedisUserCache):
    # Тут мы проверяем есть ли пользователь в БД, если да, то он обновляет state акутальными данными
    ref_id = command.args
    user_id = int(message.from_user.id)
    username = message.from_user.username

    user_cache = await get_user_cache_from_redis(redis_cache, message.from_user.id)
    if user_cache:
        user_data = user_cache
    else:
        data = await db.get_user(message.from_user.id)
        if not data:
            data = await db.get_or_create_user(message.from_user.id, message.from_user.username)
        user_data = await update_cache_fix(redis_cache, user_id, data)
        # Почему-то False
        if not data.first_visit_completed:
            data = await update_db(data, first_visit_completed=True)
            if ref_id:
                if ref_id == user_id:
                    raise ValueError
                await db.create_referral(int(ref_id), user_id)


    message_text = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end)

    #Логгирование действияю
    await db.log_user_action(message.from_user.id, "", message.text)

    await message.answer(
        text=message_text['text'],
        reply_markup=message_text['keyboard']
    )

@router.message(Command('paybeck'))
async def process_paybeck_command(message: Message, bot: Bot, command: CommandObject):
    await bot.refund_star_payment(message.from_user.id, command.args)
