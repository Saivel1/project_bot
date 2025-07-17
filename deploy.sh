  GNU nano 4.8                                                                                      deploy.sh
#!/bin/bash
# scripts/deploy.sh
echo "🚀 Развертывание VPN Bot в продакшен..."

# Остановка старых контейнеров
echo "🛑 Остановка старых контейнеров..."
docker-compose down

# Создание .env файла из примера (если не существует)
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "⚠️  Не забудьте заполнить .env файл реальными данными!"
fi

# Сборка и запуск
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up --build -d

# Проверка статуса
echo "📊 Проверка статуса контейнеров..."
docker-compose ps

# Логи
echo "📋 Последние логи бота:"
docker-compose logs -f --tail=50 telegram-bot
