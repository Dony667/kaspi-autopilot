"""Ручная проверка карточки: ничего не меняет, только показывает.

Запуск из корня проекта:
    python -m scripts.check_card 171671908 40000
где 171671908 = код товара из ссылки на карточку, 40000 = ваша минимальная цена.
"""
import sys

from app.catalog import MERCHANT_ID
from app.services.kaspi_service import fetch_offers
from app.services.price_engine import Settings, calculate_price


def main():
    master_sku, min_price = sys.argv[1], int(sys.argv[2])
    offers, total = fetch_offers(master_sku)

    print(f"Продавцов: {len(offers)} из {total}\n")
    for o in offers:
        mark = "  <-- ВЫ" if str(o["merchantId"]) == MERCHANT_ID else ""
        preorder = f", предзаказ {o['preorder']} дн." if o.get("preorder") else ""
        print(f"{o['merchantName']:<20} {o['price']:>10,.0f} ₸ "
              f"(минус бонус {o['priceMinusBonus']:,.0f}){preorder}{mark}")

    ours = [o for o in offers if str(o["merchantId"]) == MERCHANT_ID]
    current = int(ours[0]["price"]) if ours else 0
    decision = calculate_price(offers, total, current, Settings(MERCHANT_ID, min_price))

    print(f"\nВаша цена сейчас: {current:,} ₸")
    if decision.new_price:
        print(f"Бот поставил бы: {decision.new_price:,} ₸ ({decision.reason})")
    else:
        print(f"Бот ничего не менял бы: {decision.reason}")
    if decision.hit_min_price:
        print("Внимание: самый дешёвый конкурент ниже вашей минимальной цены")


if __name__ == "__main__":
    main()
