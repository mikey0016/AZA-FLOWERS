"""Mahsulot ombori: seed dagi asosiy ro'yxat + products.json dagi o'zgarishlar.

Telegram bot orqali narx/qoldiq/tavsif yangilanadi, yangi gullar qo'shiladi.
Struktura: {"added": [...], "updated": {slug: {...}}, "deleted": [slug]}.
O'chirish — yumshoq (active=0), saytda ko'rinmaydi.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

from app.seed import PRODUCTS as SEED_PRODUCTS

IMG_DEFAULTS = {
    "buketlar": {"petals": 12, "petal": "#f472b6", "center": "#ffd166", "bg": ["#fff7fb", "#ffe9f3"], "leaves": True},
    "atirgullar": {"petals": 12, "petal": "#c81e2b", "center": "#f7d078", "bg": ["#fff5f5", "#ffe3e3"], "leaves": True},
    "kompozitsiyalar": {"petals": 12, "petal": "#ffffff", "center": "#ffd977", "bg": ["#f8fafc", "#e6eef6"], "leaves": True},
    "sovgalar": {"petals": 13, "petal": "#e0576f", "center": "#5b3a29", "bg": ["#fdf2f3", "#fbe0e4"], "leaves": False},
    "xonalar": {"petals": 9, "petal": "#8bbf72", "center": "#3f7d4f", "bg": ["#f2fbf4", "#e0f5e6"], "leaves": False},
    "toy": {"petals": 15, "petal": "#ffffff", "center": "#f7e6a6", "bg": ["#f9fafb", "#eef2f7"], "leaves": True},
}


def _file(base: Path) -> Path:
    return base / "products.json"


def _load_override(base: Path) -> dict:
    try:
        d = json.loads(_file(base).read_text(encoding="utf-8"))
        return {"added": d.get("added", []), "updated": d.get("updated", {}), "deleted": d.get("deleted", [])}
    except Exception:
        return {"added": [], "updated": {}, "deleted": []}


def _save_override(base: Path, data: dict) -> None:
    _file(base).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_products(base: Path, include_inactive: bool = False) -> list[dict]:
    ov = _load_override(base)
    deleted = set(ov["deleted"])
    updated = ov["updated"]
    items = []
    for p in SEED_PRODUCTS:
        if p["slug"] in deleted:
            continue
        pp = copy.deepcopy(p)
        if p["slug"] in updated:
            pp.update(updated[p["slug"]])
        pp.setdefault("active", 1)
        items.append(pp)
    for p in ov["added"]:
        pp = copy.deepcopy(p)
        pp.setdefault("active", 1)
        items.append(pp)
    if not include_inactive:
        items = [p for p in items if p.get("active", 1)]
    return items


def get_product(base: Path, slug: str):
    for p in get_products(base, include_inactive=True):
        if p["slug"] == slug:
            return p
    return None


def upsert_field(base: Path, slug: str, field: str, value) -> dict:
    ov = _load_override(base)
    for p in ov["added"]:
        if p["slug"] == slug:
            p[field] = value
            _save_override(base, ov)
            return copy.deepcopy(p)
    if any(p["slug"] == slug for p in SEED_PRODUCTS):
        ov["updated"].setdefault(slug, {})[field] = value
        _save_override(base, ov)
        P = get_product(base, slug)
        assert P is not None
        return P
    raise KeyError(slug)


def slugify(name: str) -> str:
    t = name.lower().replace("o'", "o").replace("g'", "g").replace("'", "")
    out = []
    for ch in t:
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("-")
    s = "".join(out).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s or "gul"


def add_product(base: Path, product: dict) -> dict:
    ov = _load_override(base)
    taken = {p["slug"] for p in get_products(base, include_inactive=True)}
    slug = product.get("slug") or slugify(product.get("name", "gul"))
    i = 2
    base_slug = slug
    while slug in taken:
        slug = f"{base_slug}-{i}"
        i += 1
    product["slug"] = slug
    product.setdefault("active", 1)
    ov["added"].append(product)
    _save_override(base, ov)
    return copy.deepcopy(product)


def del_product(base: Path, slug: str) -> bool:
    """Yumshoq o'chirish: seed dagi bo'lsa deleted ro'yxatga, qo'shilgan bo'lsa olib tashlanadi."""
    ov = _load_override(base)
    for i, p in enumerate(ov["added"]):
        if p["slug"] == slug:
            ov["added"].pop(i)
            _save_override(base, ov)
            return True
    if any(p["slug"] == slug for p in SEED_PRODUCTS):
        if slug not in ov["deleted"]:
            ov["deleted"].append(slug)
            _save_override(base, ov)
        return True
    return False
