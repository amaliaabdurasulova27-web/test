"""Учебный фрагмент для тестового задания ТОЛЬКООПТ.

Python 3.10+, только стандартная библиотека. Запуск примера: python starter.py
В функции recommend_price намеренно есть ошибки. Исправьте её по правилам ниже.
sample_fetch_offers имитирует внешний источник: реальные запросы не нужны.

Контракт fetch_offers(): async-функция без аргументов, возвращает словарь
со status (success / partial / error) и offers (список предложений).
Все суммы на входе — положительные Decimal с точностью до копейки.
seller — строка; delivery_days — неотрицательное целое число или None.
Формат входных данных корректен; дополнительных проверок типов не требуется.
fetch_offers может завершиться исключением или долго ожидать ответа.
current_price — текущая цена; min_price — минимально допустимая цена.
timeout_s — положительное число секунд, по умолчанию 2.

ПРАВИЛА В ПОРЯДКЕ ПРИМЕНЕНИЯ
1. Ограничьте ожидание fetch_offers значением timeout_s. При ошибке источника,
   тайм-ауте или status != success верните текущую цену и HOLD.
2. Учитывайте предложения с известной доставкой не более 6 дней.
   Исключайте собственный магазин MYSHOP независимо от регистра букв.
3. Если подходящих предложений нет, верните текущую цену и HOLD,
   даже если текущая цена ниже min_price.
4. Минимальную цену подходящего конкурента уменьшите на 1,5% и округлите
   вниз до копейки. Рекомендация — максимум из этой суммы и min_price.
5. Если рекомендация отличается от текущей цены более чем на 30% в любую
   сторону, верните рекомендацию и REVIEW. Иначе — рекомендацию и APPLY.
   Ровно 30% допускается. REVIEW означает, что автоматическое применение
   запрещено до ручной проверки.

РЕЗУЛЬТАТ
Словарь с полями price (Decimal), decision (APPLY / REVIEW / HOLD),
reason (короткая понятная причина). Сохраните интерфейс recommend_price;
вспомогательные функции допустимы. Пример ниже после исправления должен
вернуть price = Decimal("4728.00"), decision = "APPLY".

ПРОВЕРКА
Добавьте минимум два автоматических теста: обычный расчёт и один сбой
или граничный случай на ваш выбор. Укажите команду запуска тестов.
Достаточно стандартной библиотеки; pytest также допустим.
"""


import asyncio
from decimal import Decimal, ROUND_DOWN


async def recommend_price(fetch_offers, current_price, min_price, timeout_s=2.0):
    """
    Рассчитывает рекомендованную цену на основании предложений конкурентов.

    Возвращает:
        {
            "price": Decimal,
            "decision": "APPLY" | "REVIEW" | "HOLD",
            "reason": str
        }
    """

    def hold(reason):
        return {
            "price": current_price,
            "decision": "HOLD",
            "reason": reason,
        }

    # 1. Получаем данные с ограничением времени ожидания.
    try:
        result = await asyncio.wait_for(
            fetch_offers(),
            timeout=timeout_s
        )
    except asyncio.TimeoutError:
        return hold("Превышено время ожидания источника")

    except Exception:
        return hold("Ошибка получения предложений")

    # Проверяем статус источника.
    if result.get("status") != "success":
        return hold("Источник вернул неполные или ошибочные данные")

    # 2. Фильтруем предложения.
    valid_offers = [
        offer
        for offer in result["offers"]
        if (
            offer["delivery_days"] is not None
            and offer["delivery_days"] <= 6
            and offer["seller"].strip().upper() != "MYSHOP"
        )
    ]

    # 3. Если подходящих предложений нет, сохраняем текущую цену.
    if not valid_offers:
        return hold("Нет подходящих предложений конкурентов")

    # 4. Находим минимальную цену конкурента.
    min_competitor_price = min(
        offer["price"]
        for offer in valid_offers
    )

    # Уменьшаем цену на 1.5% и округляем вниз до копейки.
    discounted_price = (
        min_competitor_price * Decimal("0.985")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_DOWN
    )

    # Рекомендация не может быть ниже минимально допустимой цены.
    recommended_price = max(
        discounted_price,
        min_price
    )

    # 5. Проверяем относительное отклонение.
    # При нулевой текущей цене деление невозможно.
    # Поэтому автоматическое применение запрещаем.
    if current_price == Decimal("0"):
        return {
            "price": recommended_price,
            "decision": "REVIEW",
            "reason": "Нулевая текущая цена требует ручной проверки",
        }

    deviation = (
        abs(recommended_price - current_price) / current_price
    )

    if deviation > Decimal("0.30"):
        return {
            "price": recommended_price,
            "decision": "REVIEW",
            "reason": "Изменение цены превышает 30%, нужна проверка",
        }

    return {
        "price": recommended_price,
        "decision": "APPLY",
        "reason": "Цена рассчитана, отклонение в допустимых пределах",
    }


async def sample_fetch_offers():
    """Имитация получения предложений конкурентов."""

    return {
        "status": "success",
        "offers": [
            {
                "seller": "myshop",
                "price": Decimal("4300.00"),
                "delivery_days": 2
            },
            {
                "seller": "PARTS",
                "price": Decimal("4800.00"),
                "delivery_days": 3
            },
            {
                "seller": "SLOW",
                "price": Decimal("4700.00"),
                "delivery_days": 8
            },
        ],
    }


if __name__ == "__main__":
    result = asyncio.run(
        recommend_price(
            sample_fetch_offers,
            current_price=Decimal("4900.00"),
            min_price=Decimal("4500.00"),
        )
    )

    print(result)

