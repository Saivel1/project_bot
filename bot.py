from refferal.refferal_logic import insert_ref, safe_add_referral, ref_base

while True:
    user_id = int(input("Введите ID пользователя: "))
    ref_id = int(input("Введите ID реферера: "))

    result = safe_add_referral(user_id, ref_id)
    print(result)
    print(ref_base)
