"""Проверка карточки через настоящий браузер. Ничего не меняет, только показывает.

Запуск из корня проекта:
    python -m scripts.browser_check <ссылка на карточку> <мин. цена> [--headless]
"""
import sys

from app.catalog import MERCHANT_ID
from app.services.browser_fetcher import fetch_offers_browser
from app.services.price_engine import Settings, calculate_price


def main():
    url, min_price = sys.argv[1], int(sys.argv[2])
    offers, total, status = fetch_offers_browser(url, headless="--headless" in sys.argv)
    print(f"Страница карточки: HTTP {status}")
    print(f"Продавцов: {len(offers)} из {total}\n")
    for o in offers:
        mark = "  <-- ВЫ" if str(o["merchantId"]) == MERCHANT_ID else ""
        pre = f", предзаказ {o['preorder']} дн." if o.get("preorder") else ""
        print(f"{o['merchantName']:<20} {o['price']:>10,.0f} ₸{pre}{mark}")

    ours = [o for o in offers if str(o["merchantId"]) == MERCHANT_ID]
    current = int(ours[0]["price"]) if ours else 0
    d = calculate_price(offers, total, current, Settings(MERCHANT_ID, min_price))
    print(f"\nВаша цена: {current:,} ₸")
    print(f"Бот поставил бы: {d.new_price:,} ₸" if d.new_price else f"Бот не менял бы: {d.reason}")


if __name__ == "__main__":
    main()
