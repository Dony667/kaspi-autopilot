from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape, quoteattr

# Казахстан живёт по UTC+5. Фиксированный сдвиг вместо zoneinfo,
# потому что на Windows zoneinfo без пакета tzdata не работает.
KZ_TZ = timezone(timedelta(hours=5))


def _check_offer(offer):
    """Не пускаем в файл явно битые данные: лучше ошибка, чем неверная цена в Kaspi."""
    if not str(offer.get("sku", "")).strip():
        raise ValueError("У товара нет sku")
    if not offer.get("city_prices"):
        raise ValueError(f"У товара {offer['sku']} нет цен")
    for city_id, price in offer["city_prices"].items():
        if not isinstance(price, int) or price <= 0:
            raise ValueError(f"Неверная цена {price!r} у товара {offer['sku']} (город {city_id})")
    if not offer.get("availabilities"):
        raise ValueError(f"У товара {offer['sku']} не указаны склады")


def build_price_xml(merchant_id, offers, now=None):
    """Собирает XML-прайс-лист в формате, который отдаёт сам кабинет Kaspi."""
    now = now or datetime.now(KZ_TZ)
    for offer in offers:
        _check_offer(offer)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kaspi_catalog xmlns="kaspiShopping" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://kaspi.kz/kaspishopping.xsd" '
        f'date="{now.strftime("%Y-%m-%d %H:%M")}">',
        f"    <company>{escape(merchant_id)}</company>",
        f"    <merchantid>{escape(merchant_id)}</merchantid>",
        "    <offers>",
    ]
    for offer in offers:
        lines.append(f"        <offer sku={quoteattr(str(offer['sku']))}>")
        lines.append(f"            <model>{escape(offer['model'])}</model>")
        brand = offer.get("brand") or ""
        lines.append(f"            <brand>{escape(brand)}</brand>" if brand else "            <brand/>")
        lines.append("            <availabilities>")
        for a in offer["availabilities"]:
            available = "yes" if a["available"] else "no"
            lines.append(
                f'                <availability available="{available}" '
                f'storeId={quoteattr(a["store_id"])} preOrder="{a.get("preorder", 0)}" '
                f'stockCount="{float(a["stock"])}"/>'
            )
        lines.append("            </availabilities>")
        lines.append("            <cityprices>")
        for city_id, price in offer["city_prices"].items():
            lines.append(f'                <cityprice cityId={quoteattr(city_id)}>{price}</cityprice>')
        lines.append("            </cityprices>")
        lines.append("        </offer>")
    lines += ["    </offers>", "</kaspi_catalog>", ""]
    return "\n".join(lines)
