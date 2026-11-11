"""Получение предложений всех продавцов в одной карточке Kaspi.

ВНИМАНИЕ: это не официальный API Kaspi, а тот же запрос, который делает
сайт kaspi.kz, когда открывает карточку. Kaspi может его изменить.
Поэтому любая странность в ответе = ошибка, а не «попробуем угадать».
"""
import json
import time
import urllib.request

OFFERS_URL = "https://kaspi.kz/yml/offer-view/offers/{master_sku}"
ALMATY_CITY_ID = "750000000"
PAGE_SIZE = 5        # столько отдаёт сам сайт, больше не просим
MAX_PAGES = 20       # защита от бесконечного цикла: максимум 100 продавцов
PAUSE_SECONDS = 1.0  # пауза между страницами, чтобы не получить 429


class KaspiError(Exception):
    """Данные получить не удалось. Цену в этом случае менять нельзя."""


def _post(url, payload, timeout=15):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_offers(master_sku, city_id=ALMATY_CITY_ID, post=_post, pause=PAUSE_SECONDS):
    """Возвращает (offers, total): все предложения карточки и сколько их должно быть."""
    url = OFFERS_URL.format(master_sku=master_sku)
    offers, total = [], None

    for page in range(MAX_PAGES):
        payload = {
            "cityId": city_id,
            "id": str(master_sku),
            "merchantUID": [],
            "limit": PAGE_SIZE,
            "page": page,
            "sortOption": "PRICE",
            "installationId": "-1",
            "highRating": None,
            "searchText": None,
            "isExcellentMerchant": False,
            "zoneId": ["Magnum_ZONE1"],
        }
        try:
            data = post(url, payload)
        except Exception as error:  # сеть, 429, 500, битый JSON
            raise KaspiError(f"страница {page}: {error}") from error

        if not isinstance(data, dict) or "offers" not in data or "total" not in data:
            raise KaspiError(f"страница {page}: неожиданный формат ответа")

        total = data["total"]
        offers.extend(data["offers"])

        if len(offers) >= total or not data["offers"]:
            break
        time.sleep(pause)

    # Один и тот же продавец не должен встречаться дважды
    ids = [o.get("merchantId") for o in offers]
    if len(ids) != len(set(ids)):
        raise KaspiError("продавцы повторяются между страницами")

    return offers, total
