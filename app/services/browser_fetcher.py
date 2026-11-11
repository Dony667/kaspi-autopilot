"""Получение всех продавцов карточки через настоящий браузер (Playwright, Chromium).

Браузер открывает карточку как обычный посетитель, а затем изнутри страницы
делает тот же запрос, что делает сам сайт kaspi.kz. Никакой маскировки:
если Kaspi откажет (403 и т.п.), мы получаем ошибку и цену не трогаем.
"""
import re

from playwright.sync_api import sync_playwright

from app.services.kaspi_service import ALMATY_CITY_ID, MAX_PAGES, PAGE_SIZE, KaspiError

FETCH_PAGE_JS = """
async ([sku, cityId, page, limit]) => {
  const r = await fetch(`/yml/offer-view/offers/${sku}`, {
    method: "POST",
    headers: {"Content-Type": "application/json", "Accept": "application/json"},
    body: JSON.stringify({
      cityId, id: sku, merchantUID: [], limit, page, sortOption: "PRICE",
      installationId: "-1", highRating: null, searchText: null,
      isExcellentMerchant: false, zoneId: ["Magnum_ZONE1"]
    })
  });
  return {status: r.status, data: r.ok ? await r.json() : null};
}
"""


def sku_from_url(url):
    """Код товара — число в конце ссылки на карточку."""
    match = re.search(r"-(\d+)/?(?:\?.*)?$", url)
    if not match:
        raise KaspiError("не нашёл код товара в конце ссылки")
    return match.group(1)


def fetch_offers_browser(card_url, city_id=ALMATY_CITY_ID, headless=True):
    """Возвращает (offers, total, page_status). При любой проблеме — KaspiError."""
    sku = sku_from_url(card_url)
    offers, total = [], None

    with sync_playwright() as p:
        # --disable-dev-shm-usage нужен в Docker: там мало общей памяти
        browser = p.chromium.launch(headless=headless, args=["--disable-dev-shm-usage"])
        try:
            page = browser.new_page()
            response = page.goto(card_url, wait_until="domcontentloaded", timeout=30000)
            page_status = response.status if response else None
            if page_status != 200:
                raise KaspiError(f"карточка открылась с кодом {page_status}")

            for n in range(MAX_PAGES):
                result = page.evaluate(FETCH_PAGE_JS, [sku, city_id, n, PAGE_SIZE])
                if result["status"] != 200:
                    raise KaspiError(f"Kaspi ответил {result['status']} на странице {n}")
                data = result["data"]
                if not isinstance(data, dict) or "offers" not in data or "total" not in data:
                    raise KaspiError(f"страница {n}: неожиданный формат ответа")
                total = data["total"]
                offers.extend(data["offers"])
                if len(offers) >= total or not data["offers"]:
                    break
                page.wait_for_timeout(1000)
        finally:
            browser.close()

    ids = [o.get("merchantId") for o in offers]
    if len(ids) != len(set(ids)):
        raise KaspiError("продавцы повторяются между страницами")
    return offers, total, page_status
