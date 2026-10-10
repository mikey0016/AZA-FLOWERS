"""To'lov tizimi (SAMA BASIC uslubida): promokodlar + karta + 50% oldindan to'lov.

Fayllar:
  promos.json  — {"KOD": {"pct": 10, "max_uses": 50, "used": 0, "active": 1}}
  payment.json — {"pay_card": "8600 ...", "prepay_pct": 50}
"""
from __future__ import annotations
import json
from pathlib import Path


def _load(base: Path, name: str, default: dict) -> dict:
    f = base / name
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return {**default, **d} if isinstance(d, dict) else dict(default)
    except Exception:
        return dict(default)


def _save(base: Path, name: str, data: dict) -> None:
    (base / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# --- payment config ---
def get_payment(base: Path) -> dict:
    return _load(base, "payment.json", {"pay_card": "", "prepay_pct": 50})


def set_payment(base: Path, **kw) -> dict:
    d = get_payment(base)
    if "pay_card" in kw:
        d["pay_card"] = str(kw["pay_card"]).strip()
    if "prepay_pct" in kw:
        try:
            d["prepay_pct"] = max(0, min(100, int(kw["prepay_pct"])))
        except (ValueError, TypeError):
            pass
    _save(base, "payment.json", d)
    return d


# --- promos ---
def _promos(base: Path) -> dict:
    try:
        d = json.loads((base / "promos.json").read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def list_promos(base: Path) -> dict:
    return _promos(base)


def check_promo(base: Path, code: str) -> dict:
    code = (code or "").strip().upper()
    if not code:
        return {"ok": False, "error": "Promokod kiritilmadi"}
    p = _promos(base).get(code)
    if not p or not p.get("active", 1):
        return {"ok": False, "error": "Promokod topilmadi"}
    try:
        pct = int(p.get("pct", 0))
    except (ValueError, TypeError):
        pct = 0
    if pct < 1 or pct > 90:
        return {"ok": False, "error": "Promokod yaroqsiz"}
    max_u = int(p.get("max_uses", 0) or 0)
    if max_u and int(p.get("used", 0) or 0) >= max_u:
        return {"ok": False, "error": "Promokod muddati tugagan"}
    return {"ok": True, "code": code, "pct": pct}


def use_promo(base: Path, code: str) -> None:
    code = (code or "").strip().upper()
    if not code:
        return
    promos = _promos(base)
    if code in promos:
        promos[code]["used"] = int(promos[code].get("used", 0) or 0) + 1
        _save(base, "promos.json", promos)


def add_promo(base: Path, code: str, pct: int, max_uses: int = 0) -> dict:
    code = (code or "").strip().upper()
    if not code:
        raise ValueError("Kod bo'sh")
    pct = int(pct)
    if pct < 1 or pct > 90:
        raise ValueError("Foiz 1–90 oralig'ida bo'lsin")
    promos = _promos(base)
    promos[code] = {"pct": pct, "max_uses": int(max_uses or 0), "used": 0, "active": 1}
    _save(base, "promos.json", promos)
    return {"code": code, **promos[code]}


def del_promo(base: Path, code: str) -> bool:
    code = (code or "").strip().upper()
    promos = _promos(base)
    if code in promos:
        del promos[code]
        _save(base, "promos.json", promos)
        return True
    return False
