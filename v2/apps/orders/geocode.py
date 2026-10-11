"""Geokodlash proksiysi: brauzer Nominatim'ga to'g'ridan-to'g'ri kira olmasa
(HTTP->HTTPS referer muammosi), server User-Agent bilan so'raydi. Kesh bilan."""
import json
import time
import urllib.parse
import urllib.request

_cache: dict = {}
CACHE_TTL = 24 * 3600


def reverse_geocode(lat: float, lon: float) -> dict:
    key = f"{round(lat, 4)},{round(lon, 4)}"
    hit = _cache.get(key)
    if hit and time.time() - hit[1] < CACHE_TTL:
        return hit[0]
    params = urllib.parse.urlencode({
        "format": "jsonv2", "lat": lat, "lon": lon, "accept-language": "uz,ru",
    })
    req = urllib.request.Request(
        "https://nominatim.openstreetmap.org/reverse?" + params,
        headers={"User-Agent": "FAXFlores/1.0 (https://azaflowers.uz)",
                 "Referer": "https://azaflowers.uz/"})
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read().decode())
    addr = data.get("address", {}) or {}
    out = {
        "ok": True,
        "road": addr.get("road", ""),
        "house_number": addr.get("house_number", ""),
        "suburb": addr.get("suburb", ""),
        "neighbourhood": addr.get("neighbourhood", ""),
        "quarter": addr.get("quarter", ""),
        "district": addr.get("district", "") or addr.get("city_district", ""),
        "city": addr.get("city", "") or addr.get("town", "") or addr.get("village", ""),
        "state": addr.get("state", "") or addr.get("county", ""),
        "iso": addr.get("ISO3166-2-lvl4", ""),
        "display": data.get("display_name", ""),
    }
    _cache[key] = (out, time.time())
    if len(_cache) > 2000:
        _cache.clear()
    return out
