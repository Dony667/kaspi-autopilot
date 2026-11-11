import os
import secrets
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from app.catalog import MERCHANT_ID, OFFERS
from app.services.browser_fetcher import fetch_offers_browser
from app.services.kaspi_service import KaspiError

app = FastAPI()

# Секретный ключ для /check задаётся в Deplexo: Environment -> CHECK_TOKEN.
# Без него страница /check не работает, чтобы посторонние не гоняли браузер.
CHECK_TOKEN = os.environ.get("CHECK_TOKEN", "")


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/price.xml")
def price_xml():
    # Импорт здесь, чтобы /price.xml работал, даже если с браузером проблемы
    from app.xml_builder import build_price_xml

    xml = build_price_xml(MERCHANT_ID, OFFERS)
    return Response(xml, media_type="application/xml")


@app.get("/check")
def check(url: str, token: str = ""):
    """Тест: может ли сервер видеть продавцов карточки. Ничего не меняет."""
    if not CHECK_TOKEN or not secrets.compare_digest(token, CHECK_TOKEN):
        raise HTTPException(status_code=403, detail="неверный token")

    started = time.time()
    try:
        offers, total, page_status = fetch_offers_browser(url)
    except KaspiError as error:
        return {"ok": False, "error": str(error), "seconds": round(time.time() - started, 1)}

    return {
        "ok": True,
        "seconds": round(time.time() - started, 1),
        "page_status": page_status,
        "total": total,
        "received": len(offers),
        "offers": [
            {
                "merchant": o.get("merchantName"),
                "merchantId": o.get("merchantId"),
                "price": o.get("price"),
                "preorder": o.get("preorder"),
                "ours": str(o.get("merchantId")) == MERCHANT_ID,
            }
            for o in offers
        ],
    }
