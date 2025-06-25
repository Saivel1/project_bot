
async def main():
    async with MarzbanBackendContext() as backend:
        while True:
            num = int(input(f'''
1 - Для создания пользователя
2 - Для удаления пользователя
3 - Чтобы получить информацию о пользователе
4 - Показать всех пользователей
5 - Сделать неактивным


Твой ответ: '''))
            if num == 1:
                nickname = input("Введи имя: ")
                res = await backend.create_user(nickname)
                print(f'Ссылка: {res['subscription_url']} Пользователь: {res['username']}.\n Успешно создан!')
            if num == 2:
                nickname = input("Введи имя: ")
                await backend.delete_user(nickname)
                print(f'Пользователь {nickname} удалён')
            if num == 3:
                nickname = input("Введи имя: ")
                res = await backend.get_user(nickname)
                if res:
                    print(f'Пользователь {res['username']} ссылка: {res['subscription_url']} | Подписка закончится: {res['expire']}')
                else:
                    print('Пользователь не найден')
            if num == 4:
                res = await backend.get_users()
                cnt = 1
                for user in res['users']:
                    print(f'{cnt}. Пользователь: {user['username']} Подписка: {user['subscription_url']}')
                    print('--------------------------------------------')
            if num == 5:
                nickname = input("Введи имя: ")
                await backend.set_inactive(nickname)
                print(f'Пользователь {nickname} неактивен')

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Тут остановились.")