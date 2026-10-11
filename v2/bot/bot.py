"""FAX Flores v2 bot — Django API ustida (SAMA UX). Stdlib only.

Env:
  BOT_TOKEN=...  ADMIN_IDS=111,222  V2_API=http://127.0.0.1:8000/api/v2
  V2_TOKEN=<staff user token>  (createsuperuser + POST /api-token-auth/ yo'q —
  tokenni /admin/ daAuthtoken orqali yoki shell'da yarating)

Ishga tushirish:  python bot.py   (v2/ ichidan)
"""
import html as _h
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texts import (  # noqa: E402
    DIV, FILTERS, HELP_TEXT, PANEL_KB, PANEL_TEXT, STATUS_UZ,
    USER_WELCOME, fm, order_keyboard, order_text, payment_instructions,
    st_label, user_status_text,
)

log = logging.getLogger("faxbot")
BASE = Path(__file__).resolve().parent
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
V2_API = os.environ.get("V2_API", "http://127.0.0.1:8000/api/v2").rstrip("/")
V2_TOKEN = os.environ.get("V2_TOKEN", "")
PAGE_SIZE = 5


def _req(url: str, data=None, headers=None, timeout=20, multipart=None):
    if multipart is not None:
        boundary, body = multipart
        headers = {**(headers or {}), "Content-Type": f"multipart/form-data; boundary={boundary}"}
        req = urllib.request.Request(url, data=body, headers=headers)
    elif data is not None:
        raw = json.dumps(data).encode()
        req = urllib.request.Request(url, data=raw,
                                     headers={**(headers or {}), "Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")


def api(method: str, path: str, data=None, timeout=20):
    return _req(V2_API + path, data=data,
                headers={"Authorization": f"Token {V2_TOKEN}"} if V2_TOKEN else {},
                timeout=timeout)


def api_upload(path: str, fields: dict, files: dict, timeout=30):
    boundary = f"fax{int(time.time() * 1000)}"
    body = b""
    for k, v in fields.items():
        if v is None:
            continue
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (fname, data, ctype) in files.items():
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'
                 f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return _req(V2_API + path, headers={"Authorization": f"Token {V2_TOKEN}"} if V2_TOKEN else {},
                multipart=(boundary, body), timeout=timeout)


def tg(method: str, payload: dict, timeout=20):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode({k: (json.dumps(v) if isinstance(v, dict) else v)
                                   for k, v in payload.items()}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def reply(cid: int, text: str):
    tg("sendMessage", {"chat_id": cid, "text": text, "parse_mode": "HTML"})


def answer(qid: str, text: str = ""):
    try:
        tg("answerCallbackQuery", {"callback_query_id": qid, "text": text}, timeout=10)
    except Exception:
        pass


def norm(u: str) -> str:
    return (u or "").strip().lower()


def is_admin(cid: int) -> bool:
    return cid in ADMIN_IDS


# ---------- offset ----------
def load_offset() -> int:
    try:
        return int((BASE / "offset.txt").read_text().strip())
    except Exception:
        return 0


def save_offset(off: int) -> None:
    try:
        (BASE / "offset.txt").write_text(str(off))
    except Exception:
        pass


# ---------- v2 helpers ----------
def v2_orders(params=""):
    try:
        r = api("GET", f"/staff/orders/{params}")
        return r if isinstance(r, list) else r.get("results", r)
    except Exception as e:
        log.warning("orders xatosi: %s", e)
        return []


def v2_order(oid: int):
    return api("GET", f"/staff/orders/{oid}/")


def v2_set_status(oid: int, status: str, by: str):
    return api("POST", f"/staff/orders/{oid}/set_status/", {"status": status, "by": by})


def v2_pay_action(pid: int, action: str, body: dict):
    return api("POST", f"/staff/payments/{pid}/{action}/", body)


def v2_set_status(oid: int, status: str, by: str = "bot"):
    return api("POST", f"/staff/orders/{oid}/set_status/", {"status": status, "by": by})


def v2_card():
    try:
        return api("GET", "/staff/payment-settings/")
    except Exception:
        return {}


# ---------- admin panel ----------
def send_panel(cid: int):
    tg("sendMessage", {"chat_id": cid, "text": PANEL_TEXT, "parse_mode": "HTML",
                       "reply_markup": PANEL_KB})


def filt_counts(orders):
    out = {}
    for f, (_, statuses) in FILTERS.items():
        out[f] = len(orders) if statuses is None else sum(1 for o in orders if o.get("status") in statuses)
    return out


def send_orders_list(cid: int, filt="pending", page=0, edit_mid=0):
    orders = v2_orders()
    if filt not in FILTERS:
        filt = "pending"
    name, statuses = FILTERS[filt]
    items = orders if statuses is None else [o for o in orders if o.get("status") in statuses]
    maxpage = max(0, (len(items) - 1) // PAGE_SIZE)
    page = max(0, min(page, maxpage))
    chunk = items[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    counts = filt_counts(orders)
    head = f"📋 <b>Buyurtmalar · {name}</b>\n<i>Jami: {len(items)} ta · Sahifa {page + 1}/{maxpage + 1}</i>"
    if not chunk:
        text = head + "\n\n📭 Bu bo'limda buyurtma yo'q."
    else:
        lines = [f"{st_label(o.get('status', ''))} <b>{o.get('no', '')}</b>\n   👤 {_h.escape(o.get('name', ''))} · 💰 <b>{fm(o.get('total', 0))} so'm</b> · <code>#{o.get('id', '')}</code>"
                 for o in chunk]
        text = head + "\n\n" + "\n\n".join(lines)
    titles = {"pending": "⏳ Kutulmoqda", "accepted": "✅ Qabul", "rejected": "❌ Rad", "all": "📋 Barchasi"}
    tabs = []
    row = []
    for f in ("pending", "accepted", "rejected", "all"):
        b = {"text": f"● {titles[f]} ({counts[f]})", "callback_data": "olist:noop"} if f == filt else \
            {"text": f"{titles[f]} ({counts[f]})", "callback_data": f"olist:{f}:0"}
        row.append(b)
        if len(row) == 2:
            tabs.append(row)
            row = []
    if row:
        tabs.append(row)
    kb_rows = [[{"text": f"#{o.get('id', '')} {o.get('no', '')}", "callback_data": f"view:{o.get('id', '')}"}] for o in chunk]
    nav = []
    if page > 0:
        nav.append({"text": "⬅️ Oldingi", "callback_data": f"olist:{filt}:{page - 1}"})
    nav.append({"text": f"· {page + 1}/{maxpage + 1} ·", "callback_data": "olist:noop"})
    if page < maxpage:
        nav.append({"text": "Keyingi ➡️", "callback_data": f"olist:{filt}:{page + 1}"})
    kb = {"inline_keyboard": tabs + kb_rows + [nav]}
    if edit_mid:
        try:
            tg("editMessageText", {"chat_id": cid, "message_id": edit_mid, "text": text,
                                   "parse_mode": "HTML", "reply_markup": kb}, timeout=15)
            return
        except Exception:
            pass
    tg("sendMessage", {"chat_id": cid, "text": text, "parse_mode": "HTML", "reply_markup": kb})


def send_stats(cid: int):
    orders = v2_orders()
    total = sum(float(o.get("total", 0) or 0) for o in orders)
    by_st: dict = {}
    for o in orders:
        by_st[o.get("status", "?")] = by_st.get(o.get("status", "?"), 0) + 1
    out = ["📊 <b>Statistika</b>", "", "📦 <b>Jami</b>",
           f"{len(orders)} ta · <b>{fm(total)} so'm</b>", "", "━━━━━━━━━━━━",
           "<b>Holatlar bo'yicha</b>", ""]
    out += [f"{st_label(s)} — <b>{n} ta</b>" for s, n in by_st.items()] or ["—"]
    reply(cid, "\n".join(out))


def send_promos(cid: int):
    try:
        promos = api("GET", "/staff/coupons/")
        promos = promos if isinstance(promos, list) else promos.get("results", [])
    except Exception:
        promos = []
    if not promos:
        reply(cid, "🎟 Promokodlar yo'q.\nYaratish: <code>/promo_add KOD FOIZ [SONI]</code>")
        return
    rows = [f"🎟 <code>{_h.escape(p['code'])}</code> — <b>{p['pct']}%</b> <i>({'cheksiz' if not p.get('max_uses') else str(p.get('used', 0)) + '/' + str(p.get('max_uses'))})</i>"
            for p in promos]
    kb = {"inline_keyboard": [[{"text": f"❌ {p['code']}", "callback_data": f"promo_del:{p['code']}"}] for p in promos]
          + [[{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    tg("sendMessage", {"chat_id": cid, "text": "🎟 <b>Promokodlar</b>\n\n" + "\n".join(rows),
                       "parse_mode": "HTML", "reply_markup": kb})


def send_products(cid: int):
    try:
        prods = api("GET", "/staff/products/")
        prods = prods if isinstance(prods, list) else prods.get("results", [])
    except Exception:
        prods = []
    if not prods:
        reply(cid, "📦 Hozircha mahsulot yo'q.\n➕ Qo'shish: /addproduct")
        return
    lines = [f"{'✅' if p.get('active') else '🚫'} <b>{_h.escape(p.get('name_uz', ''))}</b>\n   <code>{_h.escape(p.get('slug', ''))}</code> · {fm(p.get('price', 0))} · <i>{p.get('stock', 0)} dona</i>"
             for p in prods]
    kb = {"inline_keyboard": [[{"text": f"🗑 {p.get('slug', '')[:20]}", "callback_data": f"pdel:{p.get('slug', '')}"}] for p in prods[:20]]}
    tg("sendMessage", {"chat_id": cid,
                       "text": f"📦 <b>Mahsulotlar ({len(prods)} ta)</b>\n\n" + "\n\n".join(lines) + "\n\n➕ Yangi: /addproduct",
                       "parse_mode": "HTML", "reply_markup": kb})


# ---------- mijoz ----------
def send_myorders(cid: int):
    orders = [o for o in v2_orders() if o.get("tg_user") == cid][:5]
    if not orders:
        reply(cid, "📭 Buyurtmalaringiz topilmadi.")
        return
    lines = [f"{st_label(o.get('status', ''))} <b>{o.get('no', '')}</b>\n   💰 <b>{fm(o.get('total', 0))} so'm</b>" for o in orders]
    kb_rows = [[{"text": f"✅ Qabul qildim ({o.get('no', '')})", "callback_data": f"recv:{o.get('id', '')}"}]
               for o in orders if o.get("status") == "delivered"]
    tg("sendMessage", {"chat_id": cid, "text": "📦 <b>Buyurtmalarim</b>\n\n" + "\n\n".join(lines),
                       "parse_mode": "HTML",
                       **({"reply_markup": {"inline_keyboard": kb_rows}} if kb_rows else {})})


def handle_user_start(cid: int, oid_raw: str):
    try:
        oid = int(oid_raw)
    except ValueError:
        reply(cid, USER_WELCOME)
        return
    try:
        api("POST", "/staff/bot/link/", {"order_id": oid, "tg_user": cid})
        o = v2_order(oid)
    except Exception:
        reply(cid, "⛔ Buyurtma topilmadi.")
        return
    if o.get("status") == "awaiting_payment":
        reply(cid, payment_instructions(o, v2_card()))
    else:
        reply(cid, f"{user_status_text(o)}\n\n/myorders — buyurtmalarim")


def notify_user_status(o: dict, status: str, prev: str = ""):
    cid = o.get("tg_user")
    if not cid:
        return
    try:
        fresh = v2_order(o["id"])
    except Exception:
        fresh = o
    ust = user_status_text(fresh)
    text, kb = "", None
    if status == "confirmed" and prev == "awaiting_verify":
        text = f"✅ <b>To'lov tasdiqlandi!</b>\n{ust}\n⏳ Tayyorlanmoqda, kuting."
    elif status == "cancelled":
        text = f"❌ <b>Buyurtma bekor qilindi.</b>\n{ust}"
    elif status == "preparing":
        text = f"🟡 <b>Buyurtmangiz tayyorlanmoqda...</b>\n{ust}"
    elif status == "delivering":
        text = f"🚚 <b>Buyurtmangiz yo'lda!</b>\n{ust}"
    elif status == "delivered":
        text = f"📦 <b>Buyurtma yetkazildi!</b>\n{ust}\nQabul qildingizmi?"
        kb = {"inline_keyboard": [[{"text": "✅ Qabul qildim", "callback_data": f"recv:{o['id']}"}]]}
    if not text:
        return
    tg("sendMessage", {"chat_id": cid, "text": text, "parse_mode": "HTML",
                       **({"reply_markup": kb} if kb else {})})


def refresh_msgs(o: dict):
    kb = order_keyboard(o)
    try:
        detail = v2_order(o["id"])
    except Exception:
        detail = o
    for m in o.get("msgs", []) or []:
        try:
            tg("editMessageText", {"chat_id": m["chat"], "message_id": m["msg"],
                                   "text": order_text(detail), "parse_mode": "HTML",
                                   **({"reply_markup": kb} if kb else {})}, timeout=15)
        except Exception as e:
            log.warning("refresh: %s", e)


# ---------- chek ----------
def tg_file_bytes(file_id: str):
    info = tg("getFile", {"file_id": file_id}, timeout=15)
    path = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), path.rsplit("/", 1)[-1]


def handle_check(cid: int, msg: dict) -> bool:
    photos = msg.get("photo") or []
    doc = msg.get("document") or {}
    file_id = (photos[-1].get("file_id") if photos else None) or doc.get("file_id")
    if not file_id:
        return False
    if is_admin(cid):
        reply(cid, "ℹ️ Chekni mijoz yuboradi. Buyurtmalar: /orders")
        return True
    orders = [o for o in v2_orders() if o.get("tg_user") == cid and o.get("status") == "awaiting_payment"]
    if not orders:
        reply(cid, "📭 To'lov kutilayotgan buyurtmangiz topilmadi.\nAvval saytdan buyurtma berib, berilgan bot link orqali kiring.")
        return True
    o = sorted(orders, key=lambda x: x.get("id", 0))[-1]
    pay = (o.get("payment") or {})
    try:
        data, fname = tg_file_bytes(file_id)
    except Exception as e:
        log.warning("file: %s", e)
        reply(cid, "❌ Rasmni olib bo'lmadi. Qayta yuboring.")
        return True
    try:
        boundary = f"fax{int(time.time() * 1000)}"
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="payment_id"\r\n\r\n{pay.get("id", "")}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="phone"\r\n\r\n{o.get("phone", "")}\r\n').encode()
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
                 f"Content-Type: image/jpeg\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
        url = V2_API + "/receipts/"
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read().decode())
        if not res.get("ok"):
            raise RuntimeError(res.get("error", "xato"))
    except Exception as e:
        log.warning("receipt: %s", e)
        reply(cid, "❌ Chekni saqlab bo'lmadi. Qayta urining.")
        return True
    try:
        detail = v2_order(o["id"])
    except Exception:
        detail = o
    if detail.get("status") == "awaiting_payment":
        try:
            v2_set_status(o["id"], "awaiting_verify", "bot")
            detail = v2_order(o["id"])
        except Exception as e:
            log.warning("status: %s", e)
    kb = order_keyboard(detail)
    sent = []
    for admin in ADMIN_IDS:
        try:
            tg("forwardMessage", {"chat_id": admin, "from_chat_id": cid, "message_id": msg.get("message_id")}, timeout=15)
            r = tg("sendMessage", {"chat_id": admin, "text": f"📸 <b>Yangi chek!</b>\n\n{order_text(detail)}",
                                   "parse_mode": "HTML", **({"reply_markup": kb} if kb else {})}, timeout=15)
            if r.get("ok"):
                sent.append({"chat": admin, "msg": r["result"]["message_id"]})
        except Exception as e:
            log.warning("notify: %s", e)
    o["msgs"] = sent
    refresh_msgs(o)
    reply(cid, f"✅ <b>Chek qabul qilindi!</b>\n{user_status_text(detail)}\n🔎 Admin tekshirmoqda, kuting.")
    return True


# ---------- mahsulot wizard ----------
pending: dict = {}
ADD_STEPS = ["name", "cat", "price", "old", "stock", "desc", "photo"]
ADD_LBL = {"price": "Narx", "old": "Eski narx", "stock": "Qoldiq", "desc": "Tavsif"}
ADD_CANCEL = "\n\n<i>/cancel — bekor qilish</i>"
PRICE_PRESETS = [250000, 350000, 500000, 750000, 1000000, 1500000]
STOCK_PRESETS = [5, 10, 20, 50]


def parse_money(t: str):
    try:
        v = int(str(t).replace(" ", "").replace(",", ""))
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


def add_step_kb(step: str, cats: list) -> dict:
    cancel = [[{"text": "❌ Bekor qilish", "callback_data": "padd:cancel"}]]
    if step == "cat":
        rows = [[{"text": c.get("name_uz", c["slug"]), "callback_data": f"padd:cat:{c['slug']}"} for c in cats[i:i + 2]]
                for i in range(0, len(cats), 2)]
        return {"inline_keyboard": rows + cancel}
    if step == "price":
        rows = [[{"text": f"{v:,}".replace(",", " "), "callback_data": f"padd:set:price:{v}"} for v in PRICE_PRESETS[i:i + 3]]
                for i in range(0, len(PRICE_PRESETS), 3)]
        return {"inline_keyboard": rows + [[{"text": "✍️ Boshqa summa yozish", "callback_data": "padd:custom:price"}]] + cancel}
    if step == "old":
        return {"inline_keyboard": [[{"text": "➖ Chegirmasiz", "callback_data": "padd:set:old:-"}],
                [{"text": "✍️ Eski narx yozish", "callback_data": "padd:custom:old"}]] + cancel}
    if step == "stock":
        return {"inline_keyboard": [[{"text": str(v), "callback_data": f"padd:set:stock:{v}"} for v in STOCK_PRESETS],
                [{"text": "✍️ Boshqa son yozish", "callback_data": "padd:custom:stock"}]] + cancel}
    if step == "desc":
        return {"inline_keyboard": [[{"text": "⏭ O'tkazib yuborish", "callback_data": "padd:set:desc:-"}]] + cancel}
    if step == "photo":
        return {"inline_keyboard": [[{"text": "⏭ O'tkazish", "callback_data": "padd:set:photo:-"}]] + cancel}
    return {"inline_keyboard": cancel}


def add_prompt(step: str) -> str:
    n = ADD_STEPS.index(step) + 1
    return {
        "name": f"{n}/7 — Mahsulot nomini yozing:",
        "cat": f"{n}/7 — Kategoriyani tanlang:",
        "price": f"{n}/7 — Narxni tanlang (so'm):",
        "old": f"{n}/7 — Eski narx (chegirma uchun):",
        "stock": f"{n}/7 — Qoldiq sonini tanlang (dona):",
        "desc": f"{n}/7 — Qisqa tavsif yozing:",
        "photo": f"{n}/7 — Gul rasmini foto qilib yuboring:",
    }[step]


def cats_cache():
    try:
        return api("GET", "/shop/categories/")
    except Exception:
        return []


def add_send_step(cid: int):
    st = pending.get(cid)
    if not st:
        return
    if st["step"] >= len(ADD_STEPS):
        add_send_confirm(cid)
        return
    step = ADD_STEPS[st["step"]]
    tg("sendMessage", {"chat_id": cid, "text": add_prompt(step) + ADD_CANCEL, "parse_mode": "HTML",
                       "reply_markup": add_step_kb(step, cats_cache())})


def add_start(cid: int):
    pending[cid] = {"step": 0, "data": {}}
    add_send_step(cid)


def add_cancel(cid: int):
    if pending.pop(cid, None):
        reply(cid, "❌ Mahsulot qo'shish bekor qilindi.")
    else:
        reply(cid, "ℹ️ Faol wizard yo'q.")


def add_advance(cid: int):
    st = pending.get(cid)
    if not st:
        return
    st.pop("await_custom", None)
    st["step"] += 1
    add_send_step(cid)


def add_store(cid: int, field: str, value: str):
    d = pending[cid]["data"]
    if field == "name":
        if not value or len(value) < 3:
            return "⛔ Nom bo'sh bo'lmasin."
        d["name_uz"] = value[:120]
    elif field == "price":
        v = parse_money(value)
        if v is None:
            return "⛔ Narx faqat raqam bo'lsin."
        d["price"] = v
    elif field == "old":
        if value == "-":
            d["old_price"] = None
        else:
            v = parse_money(value)
            if v is None:
                return "⛔ Eski narx raqam yoki «-» bo'lsin."
            d["old_price"] = v if v and v > d.get("price", 0) else None
    elif field == "stock":
        try:
            v = int(str(value).replace(" ", ""))
            assert v >= 0
        except (ValueError, AssertionError):
            return "⛔ Son noto'g'ri. Faqat raqam yuboring."
        d["stock"] = v
    elif field == "desc":
        d["description_uz"] = "" if value == "-" else value[:500]
    elif field == "photo":
        d["photo_url"] = None if value == "-" else value[:500]
    else:
        return "⛔ Noma'lum maydon."
    return None


def add_send_confirm(cid: int):
    d = pending.get(cid, {}).get("data", {})
    kb = {"inline_keyboard": [[{"text": "✅ Saqlash", "callback_data": "padd:save"},
                               {"text": "❌ Bekor", "callback_data": "padd:cancel"}]]}
    tg("sendMessage", {"chat_id": cid,
        "text": ("🧾 <b>Yangi mahsulot</b>\n━━━━━━━━━━━━\n"
                 f"<b>Nom:</b> {_h.escape(d.get('name_uz', ''))}\n"
                 f"<b>Narx:</b> <code>{fm(d.get('price', 0))}</code>\n"
                 f"<b>Qoldiq:</b> {d.get('stock', 0)} dona\n"
                 + ("🖼 Rasm biriktirilgan\n" if d.get("photo_url") or d.get("photo_file") else "")
                 + "━━━━━━━━━━━━\nSaqlaymizmi?"),
        "parse_mode": "HTML", "reply_markup": kb})


def add_save(cid: int):
    st = pending.pop(cid, None)
    if not st:
        return
    d = dict(st["data"])
    cats = {c["slug"]: c for c in cats_cache()}
    if d.get("category") not in cats:
        d["category"] = next(iter(cats), "buketlar")
    name = d.get("name_uz", "Gul")
    base = "".join(ch.lower() if ch.isascii() and ch.isalnum() else "-" for ch in
                   name.replace("o'", "o").replace("g'", "g").replace("'", ""))
    import re
    slug = re.sub(r"-+", "-", base).strip("-") or "gul"
    fields = {"slug": slug, "name_uz": name, "price": d.get("price", 0),
              "stock": d.get("stock", 0), "category_slug": d["category"],
              "description_uz": d.get("description_uz", "")}
    if d.get("old_price"):
        fields["old_price"] = d["old_price"]
    files = {}
    if d.get("photo_file"):
        files["photo"] = (d["photo_file"][0], d["photo_file"][1], "image/jpeg")
    try:
        if files:
            r = api_upload("/staff/products/", fields, files)
        else:
            r = api("POST", "/staff/products/", fields)
        reply(cid, f"✅ <b>{_h.escape(name)}</b> qo'shildi!\nEndi u saytda ko'rinadi.\n\n➕ Yana: /addproduct\n📦 Ro'yxat: /products")
    except Exception as e:
        log.warning("save: %s", e)
        reply(cid, "❌ Saqlab bo'lmadi. Qayta urining.")


def handle_add_text(cid: int, text: str, st: dict) -> bool:
    if text.lower() in ("/cancel", "/bekor", "bekor"):
        add_cancel(cid)
        return True
    if text.startswith("/"):
        pending.pop(cid, None)
        reply(cid, "ℹ️ Mahsulot qo'shish to'xtatildi.")
        return False
    idx = st.get("step", 0)
    if idx >= len(ADD_STEPS):
        return False
    step = ADD_STEPS[idx]
    if step == "cat":
        reply(cid, "👆 Kategoriyani yuqoridagi tugmalardan tanlang.")
        add_send_step(cid)
        return True
    if step == "photo":
        if text.lower().startswith("http"):
            add_store(cid, "photo", text)
            add_advance(cid)
            return True
        if text.lower() in ("skip", "o'tkazish", "0", "-", "yo'q"):
            add_store(cid, "photo", "-")
            add_advance(cid)
            return True
        reply(cid, "📸 Rasmni foto qilib yuboring, URL yozing yoki «o'tkazish» deb yozing.")
        return True
    if step in ("price", "old", "stock", "desc", "name"):
        st.pop("await_custom", None)
        err = add_store(cid, step, text)
        if err:
            reply(cid, err + "\n\nTugmalardan tanlang yoki to'g'ri yozing.")
            return True
        add_advance(cid)
        return True
    pending.pop(cid, None)
    return False


def handle_padd(cb: dict):
    data = cb.get("data", "")
    msg = cb.get("message") or {}
    cid = (msg.get("chat") or {}).get("id")
    qid = cb.get("id")

    def ans(t: str = ""):
        answer(qid, t)

    rest = data.split(":", 2)
    what = rest[1] if len(rest) > 1 else ""
    arg = rest[2] if len(rest) > 2 else ""
    if what == "new":
        ans()
        add_start(cid)
        return
    if what == "cancel":
        ans("Bekor qilindi")
        add_cancel(cid)
        return
    if what == "save":
        ans("Saqlanmoqda...")
        add_save(cid)
        return
    st = pending.get(cid)
    if not st:
        ans("Eski tugma ⛔")
        return
    step = ADD_STEPS[st.get("step", 99)] if st.get("step", 99) < len(ADD_STEPS) else None
    if what == "cat":
        if step != "cat" or arg not in [c["slug"] for c in cats_cache()]:
            ans("Eski tugma ⛔")
            return
        st["data"]["category"] = arg
        ans("Tanlandi ✅")
        add_advance(cid)
        return
    if what == "set":
        field, _, value = arg.partition(":")
        if step != field:
            ans("Eski tugma ⛔")
            return
        err = add_store(cid, field, value)
        if err:
            ans(err)
            return
        ans("Saqlangan ✅")
        add_advance(cid)
        return
    if what == "custom":
        if step != arg:
            ans("Eski tugma ⛔")
            return
        st["await_custom"] = arg
        lbl = {"price": "Narx", "old": "Eski narx", "stock": "Qoldiq", "desc": "Tavsif"}.get(arg, arg)
        ans()
        reply(cid, f"✍️ <b>{lbl}</b> ni yozib yuboring:{ADD_CANCEL}")
        return
    ans("Noma'lum buyruq")


def handle_add_photo(cid: int, msg: dict, file_id: str) -> bool:
    st = pending.get(cid)
    if not st or st.get("step", 99) >= len(ADD_STEPS) or ADD_STEPS[st["step"]] != "photo":
        return False
    try:
        data, fname = tg_file_bytes(file_id)
    except Exception:
        reply(cid, "❌ Rasmni olib bo'lmadi. Qayta yuboring.")
        return True
    st["data"]["photo_file"] = (fname, data)
    add_advance(cid)
    return True


# ---------- xabarlar ----------
def handle_message(msg: dict):
    chat = msg.get("chat", {})
    cid = chat.get("id")
    if not cid:
        return
    frm = msg.get("from", {})
    text = (msg.get("text") or "").strip()
    photos = msg.get("photo") or []
    doc = msg.get("document") or {}
    file_id = (photos[-1].get("file_id") if photos else None) or doc.get("file_id")

    if cid in pending:
        if file_id and handle_add_photo(cid, msg, file_id):
            return
    elif file_id and handle_check(cid, msg):
        return
    if not is_admin(cid):
        if text.startswith("/start"):
            arg = text.split()[1] if len(text.split()) > 1 else ""
            if arg.startswith("ord_"):
                handle_user_start(cid, arg[4:])
                return
            reply(cid, USER_WELCOME)
            return
        if text.startswith("/myorders"):
            send_myorders(cid)
            return
        reply(cid, "ℹ️ Buyurtma uchun saytdan foydalaning.\n/myorders — buyurtmalarim")
        return
    if handle_pending_cmd(cid, text):
        return
    if text.startswith("/start"):
        arg = text.split()[1] if len(text.split()) > 1 else ""
        if arg.startswith("ord_"):
            handle_user_start(cid, arg[4:])
            return
        send_panel(cid)
        return
    if text == "/panel":
        send_panel(cid)
    elif text.startswith("/myorders"):
        send_myorders(cid)
    elif text.startswith("/orders"):
        send_orders_list(cid, "pending", 0)
    elif text.startswith("/stats"):
        send_stats(cid)
    elif text in ("/addproduct", "/mahsulot", "/add"):
        add_start(cid)
    elif text in ("/products", "/mahsulotlar"):
        send_products(cid)
    elif text.startswith("/delproduct") or text.startswith("/mahsulot_del"):
        parts = text.split()
        if len(parts) < 2:
            reply(cid, "♻️ Format: <code>/delproduct SLUG</code>")
        else:
            try:
                api("DELETE", f"/staff/products/{parts[1]}/")
                reply(cid, "🗑 O'chirildi.")
            except Exception:
                reply(cid, "⛔ Topilmadi.")
    elif text.startswith("/promo_add"):
        parts = text.split()
        if len(parts) < 3:
            reply(cid, "♻️ Format: <code>/promo_add KOD FOIZ [SONI]</code>")
        else:
            try:
                pct = int(parts[2])
            except ValueError:
                reply(cid, "⛔ Foiz butun son bo'lsin (1-90).")
                return
            mx = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
            try:
                r = api("POST", "/staff/coupons/", {"code": parts[1], "pct": pct, "max_uses": mx})
                reply(cid, f"✅ Promokod yaratildi: <b>{r.get('code')}</b> — {r.get('pct')}%")
            except Exception as e:
                reply(cid, f"⛔ {e}")
    elif text == "/promo_list":
        send_promos(cid)
    elif text.startswith("/promo_del"):
        parts = text.split()
        if len(parts) < 2:
            reply(cid, "♻️ Format: <code>/promo_del KOD</code>")
            return
        try:
            allc = api("GET", "/staff/coupons/")
            allc = allc if isinstance(allc, list) else allc.get("results", [])
            hit = next((c for c in allc if c["code"] == parts[1].upper()), None)
            if not hit:
                reply(cid, "⛔ Topilmadi.")
                return
            api("DELETE", f"/staff/coupons/{hit['id']}/")
            reply(cid, "🗑 O'chirildi.")
        except Exception:
            reply(cid, "⛔ Topilmadi.")
    elif text.startswith("/setcard"):
        parts = text.split()
        if len(parts) < 2:
            reply(cid, "♻️ Format: <code>/setcard 8600123456789012</code>")
            return
        try:
            cur = v2_card()
            cur["card_number"] = parts[1]
            api("PUT", "/staff/payment-settings/", cur)
            reply(cid, f"💳 To'lov kartasi saqlandi: <code>{_h.escape(parts[1])}</code>")
        except Exception as e:
            reply(cid, f"⛔ {e}")
    elif text == "/card":
        c = v2_card()
        reply(cid, f"💳 Karta: <code>{_h.escape(c.get('card_number', ''))}</code>" if c.get("card_number") else "💳 Karta kiritilmagan. /setcard")
    elif text == "/help":
        reply(cid, ("ℹ️ Yangi buyurtma kelganda tugmalar bilan xabar keladi.\n"
                    "➕ Mahsulot: /addproduct · 📦 Ro'yxat: /products\n"
                    "🎟 Promo: /promo_add KOD FOIZ [SONI]\n💳 Karta: /setcard KARTA"))
    elif text:
        reply(cid, "Noma'lum buyruq. /help ni bosing.")


def handle_pending_cmd(cid: int, text: str) -> bool:
    st = pending.get(cid)
    if not st:
        return False
    if text.startswith("/"):
        pending.pop(cid, None)
        reply(cid, "ℹ️ Mahsulot qo'shish to'xtatildi.")
        return False
    return handle_add_text(cid, text, st)


def handle_callback(cb: dict):
    data = cb.get("data", "")
    msg = cb.get("message") or {}
    cid = (msg.get("chat") or {}).get("id")
    mid = msg.get("message_id")
    qid = cb.get("id")
    frm = cb.get("from", {})

    if data.startswith("recv:"):
        try:
            oid = int(data.split(":")[1])
        except ValueError:
            answer(qid, "Xato")
            return
        try:
            o = v2_order(oid)
        except Exception:
            answer(qid, "Topilmadi")
            return
        if o.get("status") != "delivered" or o.get("tg_user") != frm.get("id"):
            answer(qid, "Ruxsat yo'q ⛔")
            return
        v2_set_status(oid, "closed", "mijoz")
        answer(qid, "Rahmat! 🎉")
        reply(frm.get("id"), f"🎉 <b>Buyurtma {_h.escape(o.get('no', ''))} yakunlandi!</b>")
        for admin in ADMIN_IDS:
            try:
                tg("sendMessage", {"chat_id": admin, "text": f"📦 Mijoz <b>{_h.escape(o.get('no', ''))}</b> ni qabul qildi ✅", "parse_mode": "HTML"})
            except Exception:
                pass
        return

    if not is_admin(cid):
        answer(qid, "Ruxsat yo'q ⛔")
        return

    def edit(text, kb):
        try:
            tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": text,
                                   "parse_mode": "HTML", **({"reply_markup": kb} if kb else {})}, timeout=15)
        except Exception as e:
            log.warning("edit: %s", e)

    if data.startswith("padd:"):
        handle_padd(cb)
    elif data == "products":
        send_products(cid)
        answer(qid, "")
    elif data.startswith("pdel:"):
        try:
            api("DELETE", f"/staff/products/{data.split(':', 1)[1]}/")
            answer(qid, "O'chirildi 🗑")
        except Exception:
            answer(qid, "Topilmadi")
        send_products(cid)
    elif data == "orders:10" or data.startswith("orders:"):
        parts = data.split(":")
        filt = parts[1] if len(parts) > 2 and parts[1] in ("pending", "accepted", "rejected", "all") else "pending"
        try:
            page = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            page = 0
        send_orders_list(cid, filt, page)
        answer(qid, "")
    elif data.startswith("olist:"):
        parts = data.split(":")
        filt = parts[1] if len(parts) > 1 else "pending"
        try:
            page = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            page = 0
        send_orders_list(cid, filt, page, edit_mid=mid or 0)
        answer(qid, "")
    elif data.startswith("view:"):
        try:
            o = v2_order(int(data.split(":")[1]))
            kb = order_keyboard(o)
            tg("sendMessage", {"chat_id": cid, "text": order_text(o), "parse_mode": "HTML",
                               **({"reply_markup": kb} if kb else {})})
        except Exception:
            pass
        answer(qid, "")
    elif data == "stats":
        send_stats(cid)
        answer(qid, "")
    elif data == "promos":
        send_promos(cid)
        answer(qid, "")
    elif data.startswith("promo_del:"):
        code = data.split(":", 1)[1]
        try:
            allc = api("GET", "/staff/coupons/")
            allc = allc if isinstance(allc, list) else allc.get("results", [])
            hit = next((c for c in allc if c["code"] == code), None)
            if hit:
                api("DELETE", f"/staff/coupons/{hit['id']}/")
                answer(qid, "O'chirildi 🗑")
            else:
                answer(qid, "Topilmadi")
            send_promos(cid)
        except Exception:
            answer(qid, "Topilmadi")
    elif data.startswith("order:"):
        parts = data.split(":")
        if len(parts) != 3:
            answer(qid, "Xato")
            return
        try:
            v2_set_status(int(parts[1]), parts[2], "admin")
            o = v2_order(int(parts[1]))
            notify_user_status(o, parts[2])
            answer(qid, STATUS_LABELS.get(parts[2], parts[2]))
        except Exception as e:
            answer(qid, str(e)[:60])
    else:
        answer(qid, "")


STATUS_LABELS = {
    "confirmed": "✅ Tasdiqlangan", "preparing": "🟡 Tayyorlanmoqda",
    "ready": "📦 Tayyor", "delivering": "🚚 Yo'lda",
    "delivered": "🏁 Yetkazildi", "cancelled": "❌ Bekor qilindi",
}


def dispatch(u: dict):
    if "message" in u:
        handle_message(u["message"])
    elif "callback_query" in u:
        handle_callback(u["callback_query"])


def run_polling():
    log.info("v2 bot polling boshlandi")
    while True:
        try:
            off = load_offset()
            res = tg("getUpdates", {"offset": off, "timeout": 20}, timeout=35)
            for u in res.get("result", []):
                save_offset(u.get("update_id", off) + 1)
                try:
                    dispatch(u)
                except Exception as e:
                    log.warning("update: %s", e)
        except Exception as e:
            log.warning("polling: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi")
    run_polling()
