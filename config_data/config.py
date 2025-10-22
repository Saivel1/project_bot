from dataclasses import dataclass
from environs import Env


@dataclass
class DatabaseConfig:
    database: str         # Название базы данных
    db_host: str          # URL-адрес базы данных
    db_user: str          # Username пользователя базы данных
    db_password: str      # Пароль к базе данных
    db_port: int = 5433   # Порт базы данных


@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту

@dataclass
class Config:
    tg_bot: TgBot

@dataclass
class HelpAcc:
    tg_user: str

@dataclass
class ConfigHelp:
    tg: HelpAcc

@dataclass
class BotName:
    bot_name: str

@dataclass
class Marzban:
    login: str
    password: str
    url: str

@dataclass
class MarzbanDig:
    login: str
    password: str
    url: str

@dataclass
class YooConf:
    account_id: int
    secret_key: str


def load_config(path: str | None = None) -> Config:

    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN')
        )
    )

def load_config_help(path: str | None = None) -> ConfigHelp:

    env: Env = Env()
    env.read_env(path)

    return ConfigHelp(
        tg=HelpAcc(
            tg_user=env('HELP_ACC')
        )
    )

def load_config_ref(path: str | None = None) -> BotName:

    env: Env = Env()
    env.read_env(path)

    return BotName(
        bot_name=env('BOT_NAME')
    )

def load_config_marz(path: str | None = None) -> Marzban:

    env: Env = Env()
    env.read_env(path)

    return Marzban(
        login=env('MARZBAN_USER'),
        password=env('MARZBAN_PASSWORD'),
        url=env('MARZBAN_API_URL')
    )

def load_config_marz_dig(path: str | None = None) -> MarzbanDig:

    env: Env = Env()
    env.read_env(path)

    return MarzbanDig(
        login=env('MARZBAN_USER_DIGITAL'),
        password=env('MARZBAN_PASSWORD_DIGITAL'),
        url=env('MARZBAN_API_URL_DIGITAL')
    )


def load_config_marz_mob(path: str | None = None) -> Marzban:

    env: Env = Env()
    env.read_env(path)

    return Marzban(
        login=env('MARZBAN_API_URL_MOBA'),
        password=env('MARZBAN_PASSWORD_MOBA'),
        url=env('MARZBAN_API_URL_MOBA')
    )


def load_config_db(path: str | None = None) -> DatabaseConfig:

    env: Env = Env()
    env.read_env(path)

    return DatabaseConfig(
        database=env('DB_NAME'),
        db_host=env('DB_HOST'),
        db_user=env('DB_USER'),
        db_password=env('DB_PASSWORD'),
        db_port=env('DB_PORT')
    )

def load_yookassa_config(path: str | None = None) -> YooConf:

    env: Env = Env()
    env.read_env(path)

    return YooConf(
        account_id=env('ACCOUNT_ID'),
        secret_key=env('SECRET_KEY')
    )
