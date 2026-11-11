from datetime import datetime

import pytest

from app.xml_builder import KZ_TZ, build_price_xml

OFFER = {
    "sku": "193264737",
    "model": "Статуэтка 58 см, мрамор",
    "brand": "",
    "availabilities": [
        {"store_id": "30469666_PP1", "available": True, "stock": 2},
        {"store_id": "30469666_sklad2", "available": True, "stock": 2},
    ],
    "city_prices": {"750000000": 119500},
}
NOW = datetime(2026, 11, 11, 15, 32, tzinfo=KZ_TZ)


def test_xml_matches_kaspi_export():
    xml = build_price_xml("30469666", [OFFER], now=NOW)
    assert 'date="2026-11-11 15:32"' in xml
    assert "<merchantid>30469666</merchantid>" in xml
    assert '<offer sku="193264737">' in xml
    assert '<cityprice cityId="750000000">119500</cityprice>' in xml
    assert 'storeId="30469666_PP1" preOrder="0" stockCount="2.0"' in xml
    assert 'storeId="30469666_sklad2" preOrder="0" stockCount="2.0"' in xml


@pytest.mark.parametrize("bad_price", [0, -100, None, 119500.5, "119500"])
def test_bad_price_is_rejected(bad_price):
    offer = {**OFFER, "city_prices": {"750000000": bad_price}}
    with pytest.raises(ValueError):
        build_price_xml("30469666", [offer], now=NOW)


def test_special_characters_are_escaped():
    offer = {**OFFER, "model": "Статуэтка <Мрамор> & Co"}
    xml = build_price_xml("30469666", [offer], now=NOW)
    assert "Статуэтка &lt;Мрамор&gt; &amp; Co" in xml
