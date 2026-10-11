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


def send_photo(base: Path, chat_id: int, photo: str, caption: str = "", markup: dict | None = None) -> dict:
    """Mahsulot rasmini yuborish. http(s) havola bo'lsa to'g'ridan-to'g'ri,
    lokal fayl (/static/uploads/...) bo'lsa multipart yuklash orqali."""
    import os
    s = load_settings(base)
    if not s["bot_token"]:
        raise RuntimeError("Telegram bot token sozlanmagan")
    if photo.startswith("http"):
        payload = {"chat_id": chat_id, "photo": photo, "caption": caption, "parse_mode": "HTML"}
        if markup is not None:
            payload["reply_markup"] = json.dumps(markup)
        return _api(s["bot_token"], "sendPhoto", payload, timeout=30)
    rel = photo[1:] if photo.startswith("/") else photo
    if rel.startswith("static/"):
        rel = rel[len("static/"):]
    fpath = base / "static" / rel if not rel.startswith("uploads/") else base / "static" / rel
    if not fpath.exists():
        fpath = base / rel
    boundary = f"aza{int(time.time() * 1000)}"
    fields = {"chat_id": str(chat_id), "parse_mode": "HTML", "caption": caption}
    if markup is not None:
        fields["reply_markup"] = json.dumps(markup)
    body = b""
    for k, v in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    with open(fpath, "rb") as f:
        data = f.read()
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; "
             f"filename=\"{os.path.basename(str(fpath))}\"\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    body += data + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.telegram.org/bot{s['bot_token']}/sendPhoto"
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


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
    from app.bot import st_label as _st
    DIV = "━━━━━━━━━━━━"
    no = o.get("no") or f"FAX-{o['id']}"
    lines = "\n".join(f"{i}. {_h.escape(ln['name'])} × {ln['qty']} = {_fm(ln['total'])}"
                      for i, ln in enumerate(o.get("lines", []) or [], 1)) or "—"
    parts = [
        f"🛍 <b>Buyurtma {no}</b> · <code>#{o['id']}</code>",
        _st(o.get("status", "yangi")),
        f"<i>📦 Manba: {_h.escape(o.get('source', 'sayt'))}</i>",
        DIV,
        "<b>👤 Mijoz</b>",
        "",
        f"<b>Ism:</b> {_h.escape(o.get('name', ''))}",
        f"<b>Tel:</b> <code>{_h.escape(o.get('phone', ''))}</code>",
        f"<b>Manzil:</b> {_h.escape(o.get('address', ''))}",
    ]
    if o.get("lat") and o.get("lon"):
        parts.append(f"🗺 <b>Xarita:</b> <a href=\"https://maps.google.com/?q={o['lat']},{o['lon']}\">ochish</a>")
    parts.append(f"<b>Yetkazish:</b> {_h.escape(o.get('ship_label', 'Standart'))}")
    parts.append(f"<b>To'lov:</b> {_h.escape(o.get('pay_label', 'Naqd'))}")
    parts.append(f"<b>Izoh:</b> <i>{_h.escape(o.get('note') or o.get('comment') or '—')}</i>")
    parts += [DIV, "<b>🧾 Tarkib</b>", "", f"<pre>{_h.escape(lines)}</pre>", DIV, "<b>💰 Hisob</b>", "",
              f"Mahsulotlar: {_fm(o.get('subtotal', o.get('total', 0)))} so'm"]
    if o.get("discount"):
        parts.append(f"🎟 <b>Chegirma:</b> −{_fm(o['discount'])} so'm")
    parts.append(f"Yetkazish: {_fm(o.get('ship_cost', 0))} so'm" if o.get("ship_cost") else "Yetkazish: Bepul")
    parts.append(f"💰 <b>Jami: {_fm(o.get('total', 0))} so'm</b>")
    if o.get("promo"):
        parts.append(f"🎟 <b>Promo:</b> <code>{_h.escape(o['promo'])}</code> (−{o.get('discount_pct') or '?'}%)")
    if o.get("prepay") is not None:
        parts.append(f"💳 <b>Oldindan 50%:</b> <b>{_fm(o['prepay'])}</b>")
        parts.append(f"💵 <b>Qolgan:</b> {_fm(o.get('total', 0) - o['prepay'])}")
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
