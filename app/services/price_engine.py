"""Расчёт новой цены по предложениям конкурентов в одной карточке Kaspi.

Модуль ничего не скачивает и ничего не меняет в Kaspi. Он получает список
предложений (поле offers из ответа Kaspi) и возвращает решение: менять цену или нет.
"""
import math
from dataclasses import dataclass

PRICE = "price"
PRICE_MINUS_BONUS = "priceMinusBonus"


@dataclass
class Settings:
    our_merchant_id: str      # ID нашего магазина, например "30469666"
    min_price: int            # ниже этой цены не опускаемся никогда
    step: int = 100           # на сколько тенге встаём ниже конкурента
    max_drop_pct: float = 5   # максимум снижения за один цикл, в процентах
    compare_by: str = PRICE   # PRICE (по умолчанию) или PRICE_MINUS_BONUS


@dataclass
class Decision:
    new_price: int | None     # None = цену не трогаем
    reason: str
    competitor: str | None = None
    hit_min_price: bool = False  # конкурент ниже нашего минимума, нужно уведомление


def _valid_price(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def calculate_price(offers, total, current_price, settings):
    # 1. Данные полные? Если собрали не все предложения, цену не трогаем.
    if total is None or len(offers) != total:
        return Decision(None, f"неполные данные: получено {len(offers)} из {total}")

    # 2. Все нужные цены на месте и выглядят нормально?
    fields = [PRICE] if settings.compare_by == PRICE else [PRICE, PRICE_MINUS_BONUS]
    for o in offers:
        for field in fields:
            if not _valid_price(o.get(field)):
                return Decision(
                    None,
                    f"битая цена у продавца {o.get('merchantName')}: {field}={o.get(field)!r}",
                )

    # 3. Находим себя и конкурентов.
    ours = [o for o in offers if str(o.get("merchantId")) == settings.our_merchant_id]
    rivals = [o for o in offers if str(o.get("merchantId")) != settings.our_merchant_id]
    if not ours:
        return Decision(None, "нашего предложения нет в карточке")
    if not rivals:
        return Decision(None, "конкурентов нет")

    # 4. Самый дешёвый конкурент (предзаказы тоже считаем).
    cheapest = min(rivals, key=lambda o: o[settings.compare_by])
    name = cheapest.get("merchantName")

    # 5. Целевая цена: на шаг ниже конкурента.
    if settings.compare_by == PRICE:
        target = int(cheapest[PRICE]) - settings.step
    else:
        # Kaspi принимает от нас обычную цену, поэтому переводим цель
        # из «цены минус бонус» в обычную по доле бонуса нашего же предложения.
        our = ours[0]
        bonus_ratio = our[PRICE_MINUS_BONUS] / our[PRICE]
        target = math.floor((cheapest[PRICE_MINUS_BONUS] - settings.step) / bonus_ratio)

    # 6. Минимальный порог.
    hit_min = target < settings.min_price
    target = max(target, settings.min_price)

    # 7. Цену не поднимаем: повышение будет отдельной настройкой.
    if target >= current_price:
        return Decision(None, "мы уже дешевле или равны цели", name, hit_min)

    # 8. Не больше max_drop_pct за один цикл.
    floor_this_cycle = math.ceil(current_price * (1 - settings.max_drop_pct / 100))
    new_price = max(target, floor_this_cycle)

    return Decision(new_price, f"ниже конкурента {name}", name, hit_min)
