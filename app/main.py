from fastapi import FastAPI
from fastapi.responses import Response

from app.catalog import MERCHANT_ID, OFFERS
from app.xml_builder import build_price_xml

app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/price.xml")
def price_xml():
    # Файл собирается заново при каждом запросе Kaspi из app/catalog.py
    xml = build_price_xml(MERCHANT_ID, OFFERS)
    return Response(xml, media_type="application/xml")
