from dataclasses import dataclass
from environs import Env


@dataclass
class DatabaseConfig:
    database: str         # Название базы данных
    db_host: str          # URL-адрес базы данных
    db_user: str          # Username пользователя базы данных
    db_password: str      # Пароль к базе данных


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