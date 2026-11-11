import os
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()
PRICE_FILE = "/data/price.xml"


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/price.xml")
def price_xml():
    if not os.path.exists(PRICE_FILE):
        return Response("не готов", status_code=404)
    with open(PRICE_FILE, "rb") as f:
        return Response(f.read(), media_type="application/xml")
