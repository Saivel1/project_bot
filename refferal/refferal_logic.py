from config_data.config import load_config_ref
from dataclasses import dataclass, asdict
from environs import Env
from typing import Dict, Any, List, Optional

@dataclass
class Refferal:
    invited: int
    who_invite: int
    bonus_status: bool | None


config = load_config_ref('.env')
bot_name = config.bot_name

def generate_refferal_code(invited: int) -> str:
    return f"https://t.me/{bot_name}?start={invited}"


def insert_ref(invited: int, who_invite: int) -> Dict[str, Any]:
    refferal = Refferal(invited, who_invite, False)
    return asdict(refferal)

# Структурированное хранилище
ref_base: List[Dict[str, Any]] = []

def is_user_already_invited(invited: int) -> bool:
    """Проверяет, был ли пользователь уже приглашен"""
    return any(ref['invited'] == invited for ref in ref_base)

def get_referrer(invited: int) -> Optional[Dict[str, Any]]:
    """Получает реферера пользователя"""
    for ref in ref_base:
        if ref['invited'] == invited:
            return ref
    return None

def would_create_cycle(invited: int, who_invite: int) -> bool:
    """Проверяет, создаст ли новая связь циклическую зависимость"""
    # Если who_invite уже приглашен кем-то в цепочке от invited, то это цикл

    def get_all_referrers(current_user: int, visited: set) -> set:
        """Получает всех рефереров в цепочке"""
        if current_user in visited:
            return set()  # Избегаем бесконечной рекурсии

        visited.add(current_user)
        referrers = set()

        # Находим всех, кто пригласил current_user
        for ref in ref_base:
            if ref['invited'] == current_user:
                referrers.add(ref['who_invite'])
                # Рекурсивно добавляем рефереров рефереров
                referrers.update(get_all_referrers(ref['who_invite'], visited.copy()))

        return referrers

    # Получаем всех рефереров who_invite
    all_referrers_of_ref = get_all_referrers(who_invite, set())

    # Если invited уже является реферером who_invite, то создание связи invited -> who_invite создаст цикл
    return invited in all_referrers_of_ref

def append_ref_base(invited: int, who_invite: int) -> Dict[str, Any]:
    """Добавляет реферальную связь с проверками"""

    print(f"🔍 Проверяем возможность добавления: {invited} -> {who_invite}")

    # Проверка 1: Пользователь не может пригласить сам себя
    if invited == who_invite:
        raise ValueError("Пользователь не может быть реферером самого себя")

    # Проверка 2: Пользователь уже был приглашен
    if is_user_already_invited(invited):
        existing_ref = get_referrer(invited)
        raise ValueError(f"Пользователь {invited} уже был приглашен пользователем {existing_ref['who_invite']}")

    # Проверка 3: Проверяем циклические зависимости
    if would_create_cycle(invited, who_invite):
        raise ValueError(f"Создание связи {invited} -> {who_invite} приведет к циклической зависимости")

    ref_data = insert_ref(invited, who_invite)
    ref_base.append(ref_data)
    print(f"✅ Связь добавлена: {ref_data}")
    return ref_data

async def safe_add_referral(invited: int, who_invite: int):
    """Безопасное добавление реферальной связи"""
    try:
        result = append_ref_base(invited, who_invite)
        print(f"✅ Пользователь {invited} успешно привязан к рефереру {who_invite}")
        print(f"Результат: {result}")
        print(f"Текущая база: {ref_base}")
        return result
    except ValueError as e:
        print(f"❌ Ошибка: {e}")
        return None