from typing import Any, Dict, List


async def reward_add(dict_list: List[Dict[str, Any]], who_invite: int) -> int:
    cnt = 0
    for ref in dict_list:
        if ref['who_invite'] == who_invite and ref['bonus_status'] == True:
            cnt += 1

    return cnt

async def switch_to_used(dict_list: List[Dict[str, Any]], who_invite: int) -> None:

    for ref in dict_list:
        if ref['who_invite'] == who_invite and ref['bonus_status'] == True:
            ref.update({'bonus_status': None})

    return None

async def reward_set(dict_list: List[Dict[str, Any]], invited: int) -> None:

    for ref in dict_list:
        if ref['invited'] == invited and ref['bonus_status'] == False:
            ref.update({'bonus_status': True})

    return None