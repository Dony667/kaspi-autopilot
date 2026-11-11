from app.services.price_engine import PRICE_MINUS_BONUS, Settings, calculate_price

S = Settings(our_merchant_id="30469666", min_price=40000, step=100, max_drop_pct=5)


def offer(mid, name, price):
    # Бонус Kaspi в примерах около 3%, как в реальных ответах.
    return {"merchantId": mid, "merchantName": name,
            "price": price, "priceMinusBonus": round(price * 0.97)}


# Карточка магнита, как в реальном ответе Kaspi (7 продавцов).
MAGNET = [
    offer("30486597", "LUZA", 18650),
    offer("30428785", "MegaSapa", 18651),
    offer("30356378", "ИП ЕСЕНБАЙ", 18675),
    offer("30334605", "Rich Market.", 20000),
    offer("30418439", "TripleA store", 20900),
    offer("30443263", "Yoko магазин", 24000),
    offer("30469666", "S&D store", 50000),
]


def test_magnet_first_cycle_drops_only_5_percent():
    d = calculate_price(MAGNET, 7, 50000, S)
    assert d.new_price == 47500
    assert d.competitor == "LUZA"
    assert d.hit_min_price  # LUZA дешевле нашего минимума 40 000


def test_never_below_min_price():
    price = 50000
    for _ in range(20):  # много циклов подряд
        d = calculate_price(MAGNET, 7, price, S)
        if d.new_price is None:
            break
        price = d.new_price
    assert price == 40000


def test_incomplete_data_no_change():
    d = calculate_price(MAGNET[:5], 7, 50000, S)  # вторую страницу не скачали
    assert d.new_price is None
    assert "неполные" in d.reason


def test_bad_price_no_change():
    bad = MAGNET[:-1] + [{**MAGNET[-1], "price": 0}]
    assert calculate_price(bad, 7, 50000, S).new_price is None


def test_we_are_not_in_card_no_change():
    assert calculate_price(MAGNET[:-1], 6, 50000, S).new_price is None


def test_no_competitors_no_change():
    assert calculate_price([MAGNET[-1]], 1, 50000, S).new_price is None


def test_example_from_spec():
    # Наш 15 000, конкуренты 14 800 / 14 900 / 14 600, шаг 100, минимум 14 000.
    s = Settings(our_merchant_id="1", min_price=14000, step=100, max_drop_pct=10)
    offers = [offer("1", "мы", 15000), offer("2", "А", 14800),
              offer("3", "Б", 14900), offer("4", "В", 14600)]
    d = calculate_price(offers, 4, 15000, s)
    assert d.new_price == 14500
    assert d.competitor == "В"
    assert not d.hit_min_price


def test_example_from_spec_by_price_minus_bonus():
    s = Settings(our_merchant_id="1", min_price=14000, step=100, max_drop_pct=10,
                 compare_by=PRICE_MINUS_BONUS)
    offers = [offer("1", "мы", 15000), offer("2", "А", 14800),
              offer("3", "Б", 14900), offer("4", "В", 14600)]
    assert calculate_price(offers, 4, 15000, s).new_price == 14496


def test_real_response_without_bonus_works_by_price():
    # Так Kaspi отвечает боту: priceMinusBonus = None у всех
    offers = [{**o, "priceMinusBonus": None} for o in MAGNET]
    d = calculate_price(offers, 7, 47500, S)
    assert d.new_price == 45125
    assert d.competitor == "LUZA"


def test_bonus_mode_without_bonus_no_change():
    s = Settings(our_merchant_id="30469666", min_price=40000, compare_by=PRICE_MINUS_BONUS)
    offers = [{**o, "priceMinusBonus": None} for o in MAGNET]
    d = calculate_price(offers, 7, 47500, s)
    assert d.new_price is None
    assert "priceMinusBonus" in d.reason


def test_already_cheapest_no_change():
    offers = [offer("30469666", "S&D store", 41000), offer("2", "А", 45000)]
    assert calculate_price(offers, 2, 41000, S).new_price is None
