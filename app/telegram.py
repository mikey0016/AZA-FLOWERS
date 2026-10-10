"""Telegram bot orqali adminlarga buyurtma xabari yuborish.

Sozlash (2 usuldan biri):
  1) Loyiha ildizida `telegram.json` fayli:
       {"bot_token": "123456:ABC...", "admin_chat_ids": [111111, 222222]}
  2) Muhit o'zgaruvchilari:
       TELEGRAM_BOT_TOKEN=...  TELEGRAM_ADMIN_IDS=111111,222222

Admin chat ID ni bilish uchun:
  1. @BotFather da bot yarating, tokenni oling.
  2. Har bir admin botni ochib Start tugmasini bossin.
  3. Serverga tokenni qo'yib, GET /api/telegram/updates oching —
     ro'yxatda har bir adminning chat ID si ko'rinadi.
"""
from __future__ import annotations
import html as _h
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

log = logging.getLogger("aza.telegram")


def load_settings(base: Path) -> dict:
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    ids: list[int] = []
    raw = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()
    if raw:
        ids = [int(x) for x in raw.split(",") if x.strip().isdigit()]
    f = base / "telegram.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            token = token or str(data.get("bot_token", "")).strip()
            file_ids = data.get("admin_chat_ids", []) or []
            if not ids:
                ids = [int(x) for x in file_ids]
        except Exception as e:
            log.warning("telegram.json o'qilmadi: %s", e)
    return {"bot_token": token, "admin_chat_ids": ids}


def _api(token: str, method: str, payload: dict, timeout: int = 12) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call_api(base: Path, method: str, payload: dict, timeout: int = 30) -> dict:
    """Bot API ga to'g'ridan-to'g'ri murojaat (bot panel uchun)."""
    s = load_settings(base)
    if not s["bot_token"]:
        raise RuntimeError("Telegram bot token sozlanmagan")
    return _api(s["bot_token"], method, payload, timeout=timeout)


def get_updates(base: Path) -> list[dict]:
    """Botga yozgan odamlar ro'yxati (chat ID aniqlash uchun)."""
    s = load_settings(base)
    if not s["bot_token"]:
        return []
    try:
        res = _api(s["bot_token"], "getUpdates", {"timeout": 0})
    except Exception as e:
        log.warning("getUpdates xatosi: %s", e)
        return []
    seen: dict[int, dict] = {}
    for u in res.get("result", []):
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat", {})
        cid = chat.get("id")
        if cid and cid not in seen:
            seen[cid] = {
                "chat_id": cid,
                "username": "@" + chat.get("username", "?"),
                "name": f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip(),
                "type": chat.get("type"),
            }
    return list(seen.values())


def _fm(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def order_text(o: dict) -> str:
    no = o.get("no") or f"AZA-{o['id']}"
    st = o.get("status", "yangi")
    parts = [
        f"🧾 <b>Buyurtma {no} · #{o['id']}</b>",
        f"Holati: {st}",
        f"👤 Ism: {_h.escape(o['name'])}",
        f"📞 Tel: {_h.escape(o['phone'])}",
        f"📍 Manzil: {_h.escape(o['address'])}",
    ]
    if o.get("ship_label"):
        parts.append(f"🚚 Yetkazish: {_h.escape(o['ship_label'])}")
    if o.get("pay_label"):
        parts.append(f"💳 To'lov: {_h.escape(o['pay_label'])}")
    if o.get("note"):
        parts.append(f"📝 Izoh: {_h.escape(o['note'])}")
    if o.get("lat") and o.get("lon"):
        parts.append(f"🗺 Xarita: <a href=\"https://maps.google.com/?q={o['lat']},{o['lon']}\">ochish</a>")
    if o.get("comment"):
        parts.append(f"💬 Izoh: {_h.escape(o['comment'])}")
    parts.append("")
    for i, ln in enumerate(o["lines"], 1):
        parts.append(f"{i}. {_h.escape(ln['name'])} × {ln['qty']} — {_fm(ln['total'])} so'm")
    parts += [
        "",
        f"Mahsulotlar: {_fm(o.get('subtotal', o['total']))} so'm",
    ]
    if o.get("discount"):
        parts.append(f"🎟 Chegirma: −{_fm(o['discount'])} so'm")
    parts.append(f"Yetkazish: {_fm(o.get('ship_cost', 0))} so'm" if o.get("ship_cost") else "Yetkazish: Yandex'ga alohida")
    parts.append(f"💰 <b>Jami: {_fm(o['total'])} so'm</b>")
    if o.get("promo"):
        parts.append(f"🎟 Promo: <code>{_h.escape(o['promo'])}</code> (−{o.get('discount_pct', 0)}%)")
    if o.get("prepay") is not None:
        parts.append(f"💳 Oldindan: {_fm(o['prepay'])} so'm")
        parts.append(f"💵 Qolgan: {_fm(o['total'] - o['prepay'])} so'm")
    parts.append(f"🕒 {o['created_at']}")
    return "\n".join(parts)


def order_bot_url(base: Path, oid: int) -> str:
    """Mijoz chek yuborishi uchun bot havolasi (start=ord_ID)."""
    try:
        info = _api(load_settings(base)["bot_token"], "getMe", {}, timeout=10)
        uname = (info.get("result") or {}).get("username")
        if uname:
            return f"https://t.me/{uname}?start=ord_{oid}"
    except Exception as e:
        log.warning("getMe xatosi: %s", e)
    return f"https://t.me/azaflowers?start=ord_{oid}"


def send_message(base: Path, chat_id: int, text: str) -> bool:
    """Bitta manzilga xabar yuborish."""
    s = load_settings(base)
    if not s["bot_token"]:
        return False
    try:
        res = _api(s["bot_token"], "sendMessage",
                   {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        return bool(res.get("ok"))
    except Exception as e:
        log.warning("Telegram yuborilmadi (%s): %s", chat_id, e)
        return False


def broadcast_order(base: Path, text: str) -> dict:
    """Barcha adminlarga yuborish. Token/ID yo'q bo'lsa jim o'tkazib yuboradi."""
    s = load_settings(base)
    out = {"configured": bool(s["bot_token"]), "sent": [], "failed": []}
    if not s["bot_token"] or not s["admin_chat_ids"]:
        return out
    for cid in s["admin_chat_ids"]:
        try:
            res = _api(s["bot_token"], "sendMessage",
                       {"chat_id": cid, "text": text, "parse_mode": "HTML"})
            (out["sent"] if res.get("ok") else out["failed"]).append(cid)
        except Exception as e:
            log.warning("Telegram yuborilmadi (%s): %s", cid, e)
            out["failed"].append(cid)
    return out


def notify_admins(base: Path, order: dict) -> dict:
    """Yangi buyurtma + ✅ Qabul qildim tugmasi bilan yuborish."""
    s = load_settings(base)
    out = {"configured": bool(s["bot_token"]), "sent": [], "failed": []}
    if not s["bot_token"] or not s["admin_chat_ids"]:
        return out
    kb = json.dumps({"inline_keyboard": [[{
        "text": "✅ Qabul qildim", "callback_data": f"accept:{order['id']}"}]]})
    for cid in s["admin_chat_ids"]:
        try:
            res = _api(s["bot_token"], "sendMessage", {
                "chat_id": cid, "text": order_text(order),
                "parse_mode": "HTML", "reply_markup": kb})
            (out["sent"] if res.get("ok") else out["failed"]).append(cid)
        except Exception as e:
            log.warning("Telegram yuborilmadi (%s): %s", cid, e)
            out["failed"].append(cid)
    return out


def download_photo(base: Path, file_id: str, slug: str) -> str:
    """Telegram dagi rasmni yuklab static/uploads ga saqlaydi. Sayt URL ini qaytaradi."""
    s = load_settings(base)
    if not s["bot_token"]:
        raise RuntimeError("Telegram bot token sozlanmagan")
    info = _api(s["bot_token"], "getFile", {"file_id": file_id}, timeout=15)
    fpath = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{s['bot_token']}/{fpath}"
    d = base / "static" / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob(slug + "_*"):
        try:
            old.unlink()
        except Exception:
            pass
    name = f"{slug}_{int(time.time())}.jpg"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r, open(d / name, "wb") as f:
        f.write(r.read())
    return f"/static/uploads/{name}"
