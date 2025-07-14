#!/bin/bash

# Скрипт для удаления всех таблиц из PostgreSQL и очистки кэша Redis
# Автор: Скрипт очистки БД
# Дата: $(date)

# Настройки подключения к PostgreSQL
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="bot_user"
DB_USER="bot_user"
DB_PASSWORD="1234"

# Настройки подключения к Redis
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD=""  # Оставьте пустым если пароль не установлен

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Скрипт очистки PostgreSQL и Redis ===${NC}"

# Функция для очистки PostgreSQL
cleanup_postgresql() {
    echo -e "${YELLOW}Начинаю очистку PostgreSQL...${NC}"

    # Проверка доступности PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}Ошибка: psql не найден. Установите PostgreSQL клиент.${NC}"
        return 1
    fi

    # Экспорт пароля для автоматической аутентификации
    export PGPASSWORD="$DB_PASSWORD"

    # Проверка подключения к базе данных
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
        echo -e "${RED}Ошибка: Не удается подключиться к PostgreSQL${NC}"
        return 1
    fi

    echo "Подключение к PostgreSQL успешно установлено"

    # Получение списка всех таблиц
    TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public';
    " | tr -d ' ')

    if [ -z "$TABLES" ]; then
        echo -e "${GREEN}В схеме 'public' нет таблиц для удаления${NC}"
    else
        echo "Найдены следующие таблицы для удаления:"
        echo "$TABLES"

        # Подтверждение удаления
        read -p "Вы уверены, что хотите удалить ВСЕ таблицы? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            # Отключение проверки внешних ключей
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
                SET session_replication_role = 'replica';
            "

            # Удаление всех таблиц
            for table in $TABLES; do
                if [ ! -z "$table" ]; then
                    echo "Удаляю таблицу: $table"
                    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
                        DROP TABLE IF EXISTS \"$table\" CASCADE;
                    "
                fi
            done

            # Включение проверки внешних ключей
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
                SET session_replication_role = 'origin';
            "

            echo -e "${GREEN}Все таблицы успешно удалены из PostgreSQL${NC}"
        else
            echo -e "${YELLOW}Удаление таблиц отменено${NC}"
        fi
    fi

    # Очистка переменной пароля
    unset PGPASSWORD
}

# Функция для очистки Redis
cleanup_redis() {
    echo -e "${YELLOW}Начинаю очистку Redis...${NC}"

    # Проверка доступности Redis
    if ! command -v redis-cli &> /dev/null; then
        echo -e "${RED}Ошибка: redis-cli не найден. Установите Redis клиент.${NC}"
        return 1
    fi

    # Формирование команды подключения
    REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT"
    if [ ! -z "$REDIS_PASSWORD" ]; then
        REDIS_CMD="$REDIS_CMD -a $REDIS_PASSWORD"
    fi

    # Проверка подключения к Redis
    if ! $REDIS_CMD ping &> /dev/null; then
        echo -e "${RED}Ошибка: Не удается подключиться к Redis${NC}"
        return 1
    fi

    echo "Подключение к Redis успешно установлено"

    # Получение информации о базах данных
    DBS_INFO=$($REDIS_CMD INFO keyspace)

    if [ -z "$DBS_INFO" ]; then
        echo -e "${GREEN}Redis уже пуст${NC}"
    else
        echo "Найдены данные в Redis:"
        echo "$DBS_INFO"

        # Подтверждение очистки
        read -p "Вы уверены, что хотите очистить ВСЕ данные из Redis? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            # Очистка всех баз данных Redis
            $REDIS_CMD FLUSHALL
            echo -e "${GREEN}Все данные успешно удалены из Redis${NC}"
        else
            echo -e "${YELLOW}Очистка Redis отменена${NC}"
        fi
    fi
}

# Основная функция
main() {
    echo -e "${YELLOW}Выберите действие:${NC}"
    echo "1) Очистить только PostgreSQL"
    echo "2) Очистить только Redis"
    echo "3) Очистить и PostgreSQL, и Redis"
    echo "4) Выйти"

    read -p "Введите номер действия (1-4): " choice

    case $choice in
        1)
            cleanup_postgresql
            ;;
        2)
            cleanup_redis
            ;;
        3)
            cleanup_postgresql
            cleanup_redis
            ;;
        4)
            echo -e "${GREEN}Выход из программы${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Неверный выбор${NC}"
            exit 1
            ;;
    esac
}

# Проверка на запуск от root (для некоторых операций может потребоваться)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Предупреждение: Скрипт запущен от root${NC}"
fi

# Запуск основной функции
main

echo -e "${GREEN}Скрипт завершен${NC}"