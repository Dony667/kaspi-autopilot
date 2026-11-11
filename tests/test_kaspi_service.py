import pytest

from app.services.kaspi_service import KaspiError, fetch_offers


def make_offers(n, start=0):
    return [{"merchantId": str(1000 + i), "merchantName": f"m{i}",
             "price": 100 + i, "priceMinusBonus": 97 + i} for i in range(start, start + n)]


def fake_kaspi(pages, total):
    """Подделка Kaspi: отдаёт заранее заданные страницы и считает запросы."""
    calls = []

    def post(url, payload):
        calls.append(payload["page"])
        return {"offers": pages[payload["page"]], "total": total}

    return post, calls


def test_collects_all_pages():
    post, calls = fake_kaspi([make_offers(5), make_offers(2, 5)], total=7)
    offers, total = fetch_offers("171671908", post=post, pause=0)
    assert total == 7 and len(offers) == 7
    assert calls == [0, 1]


def test_single_page_one_request():
    post, calls = fake_kaspi([make_offers(1)], total=1)
    offers, total = fetch_offers("185180220", post=post, pause=0)
    assert len(offers) == 1 and calls == [0]


def test_network_error_raises():
    def post(url, payload):
        raise OSError("HTTP 429 Too Many Requests")

    with pytest.raises(KaspiError):
        fetch_offers("171671908", post=post, pause=0)


def test_strange_response_raises():
    with pytest.raises(KaspiError):
        fetch_offers("171671908", post=lambda u, p: {"error": "x"}, pause=0)


def test_duplicate_merchants_raise():
    post, _ = fake_kaspi([make_offers(5), make_offers(2, 4)], total=7)  # 1004 дважды
    with pytest.raises(KaspiError):
        fetch_offers("171671908", post=post, pause=0)


def test_short_data_detected_by_price_engine():
    # Kaspi сказал 7, а вторая страница пустая: собрали 5 из 7
    post, _ = fake_kaspi([make_offers(5), []], total=7)
    offers, total = fetch_offers("171671908", post=post, pause=0)
    assert len(offers) == 5 and total == 7  # price_engine увидит это и не тронет цену
