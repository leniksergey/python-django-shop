from celery import shared_task


@shared_task
def process_payment(order_id, number):
    """
    Фиктивный платёжный сервис.

    Логика по ТЗ:
    - номер чётный И НЕ заканчивается на 0 → оплата подтверждается;
    - номер нечётный ИЛИ заканчивается на 0 → ошибка оплаты.

    Возвращает:
    - True — оплата успешна;
    - строка с текстом ошибки — оплата не прошла.
    """
    is_even = number.isdigit() and int(number) % 2 == 0
    not_zero_end = not number.endswith("0")

    if is_even and not_zero_end:
        return True

    # Формируем понятный текст ошибки
    if not is_even:
        return "Оплата отклонена: номер должен быть чётным"
    if not not_zero_end:
        return "Оплата отклонена: номер не должен заканчиваться на 0"

    return "Оплата отклонена платёжной системой"
