# Товары, которые попадут в XML-прайс-лист для Kaspi.
# ВАЖНО: Kaspi снимает с продажи всё, чего нет в загруженном прайс-листе.
# Поэтому здесь должны быть ВСЕ ваши товары, а не только тот, который тестируем.

MERCHANT_ID = "30469666"

OFFERS = [
    {
        "sku": "193264737",
        "model": "Статуэтка 58 см, мрамор",
        "brand": "",
        "availabilities": [
            {"store_id": "30469666_PP1", "available": True, "stock": 2},
            {"store_id": "30469666_sklad2", "available": True, "stock": 2},
        ],
        "city_prices": {"750000000": 119500},
    },
    {
        "sku": "171671908_827927985",
        "model": "Noname магнит-сувенир Магнитный музыкальный бокс Michael Jackson 1 шт",
        "brand": "Noname",
        "availabilities": [
            {"store_id": "30469666_PP1", "available": True, "stock": 1},
            {"store_id": "30469666_sklad2", "available": True, "stock": 1},
        ],
        "city_prices": {"750000000": 50000},
    },
]
