import asyncio
from datetime import datetime
from aiogram.exceptions import TelegramForbiddenError
from db.db_inject import db_manager as db
from db.db_model import User

async def check_and_send_subscription_reminders(bot):
   """Проверяет пользователей и отправляет напоминания за день до окончания подписки"""

   while True:
       try:
           current_time = int(datetime.now().timestamp())
           tomorrow_time = current_time + 86400  # +24 часа

           # Получаем пользователей, у которых подписка заканчивается завтра (±1 час)
           query = """
           SELECT user_id, username, subscription_end
           FROM users
           WHERE subscription_end BETWEEN $1 AND $2
           AND status_bot = 'active'
           """

           async with db.pool.acquire() as conn:
               users = await conn.fetch(query, tomorrow_time - 3600, tomorrow_time + 3600)

           print(f"🔍 Найдено {len(users)} пользователей с истекающей завтра подпиской")

           for user_row in users:
               user_id = user_row['user_id']
               subscription_end = user_row['subscription_end']

               # Вычисляем когда заканчивается подписка
               end_date = datetime.fromtimestamp(subscription_end)
               end_date_str = end_date.strftime("%d.%m.%Y в %H:%M")

               text = f"""⚠️ НАПОМИНАНИЕ О ПОДПИСКЕ

🕐 Ваша подписка заканчивается завтра!
📅 Дата окончания: {end_date_str}

💡 Не забудьте продлить подписку, чтобы продолжить пользоваться VPN!

Для пользователей с IOS | MacOS можно купить звёзды в этом боте: @PremiumBot
🔄 Для продления используйте /start"""

               try:
                   await bot.send_message(user_id, text)
                   print(f"✅ Напоминание отправлено пользователю {user_id}")

                   # Логируем отправку
                   await db.log_user_action(user_id, "SUBSCRIPTION_REMINDER", "Отправлено напоминание о подписке")

               except TelegramForbiddenError:
                   print(f"🚫 Пользователь {user_id} заблокировал бота!")

                   # Обновляем статус в БД
                   user = await db.get_user(user_id)
                   if user:
                       updated_user = User(
                           user_id=user.user_id,
                           username=user.username,
                           status_bot="BLOCKED",
                           created_at=user.created_at,
                           balance=user.balance,
                           link=user.link,
                           trial=user.trial,
                           trial_end=user.trial_end,
                           referral_count=user.referral_count,
                           first_visit_completed=user.first_visit_completed,
                           subscription_end=user.subscription_end
                       )
                       await db.update_user(updated_user)
                       await db.log_user_action(user_id, "BLOCKED_BOT", "Заблокировал бота при напоминании")

               except Exception as e:
                   print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

               # Небольшая задержка между отправками
               await asyncio.sleep(1)

       except Exception as e:
           print(f"💥 Ошибка в проверке подписок: {e}")

       # Проверяем каждый час
       await asyncio.sleep(3600)
