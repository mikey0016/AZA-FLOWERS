"""Telegram admin panel — buyurtmalarni bot orqali boshqarish.

Ishlashi: server ishga tushganda bot fon jarayonda polling boshlaydi.
- /start — ro'yxatdan o'tish + menyu
- 🧾 So'nggi buyurtmalar, 📊 Bugungi hisobot, 📦 Qoldiqlar
- Saytdan tushgan buyurtma xabarida ✅ Qabul qildim tugmasi —
  bosilsa buyurtma orders.json da "qabul" deb belgilanadi.
- Whitelist dagi (@adminlar) yangi chat ID avtomatik saqlanadi.
"""
from __future__ import annotations
import html as _h
import json
import logging
import time
from datetime import date
from pathlib import Path

from app import telegram as tg
from app.seed import CATEGORIES, CONTACT
from app import store as pstore

log = logging.getLogger("aza.bot")

MENU = [["🧾 So'nggi buyurtmalar", "📊 Bugungi hisobot"], ["🌷 Mahsulotlar", "📦 Qoldiqlar"], ["🎟 Promokodlar", "💳 Karta"], ["ℹ️ Yordam"]]

HELP = (
    "ℹ️ <b>AZA FLOWERS — admin panel</b>\n\n"
    "🧾 <b>So'nggi buyurtmalar</b> — oxirgi buyurtmalar ro'yxati\n"
    "📊 <b>Bugungi hisobot</b> — bugungi son va summa\n"
    "📦 <b>Qoldiqlar</b> — ombordagi mahsulotlar soni\n"
    "🌷 <b>Mahsulotlar</b> — yangi gul qo'shish, narx/qoldiq/tavsif tahrirlash\n"
    "🎟 <b>Promokodlar</b> — chegirma kodlari ro'yxati\n"
    "💳 <b>Karta</b> — to'lov kartasi raqami\n\n"
    "Buyruqlar:\n"
    "/orders — buyurtmalar (tugmalar bilan)\n"
    "/stats — statistika\n"
    "/promo_add KOD FOIZ [SONI] — masalan: <code>/promo_add NAVROZ10 10 50</code>\n"
    "/promo_list — promokodlar\n"
    "/promo_del KOD — o'chirish\n"
    "/setcard 8600123456789012 — to'lov kartasi\n"
    "/card — hozirgi karta\n\n"
    "Saytdan tushgan buyurtma chek yuborilgach shu yerga keladi. "
    "<b>✅ Chekni tasdiqlash</b> yoki <b>❌ Rad etish</b> tugmasini bosing."
)


def _fm(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def norm(u: str) -> str:
    return (u or "").strip().lstrip("@").lower()


# --- fayllar ---
def _orders(base: Path) -> list:
    try:
        return json.loads((base / "orders.json").read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_orders(base: Path, orders: list) -> None:
    (base / "orders.json").write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")


def load_offset(base: Path) -> int:
    try:
        return int((base / "telegram_offset.txt").read_text().strip())
    except Exception:
        return 0


def save_offset(base: Path, off: int) -> None:
    try:
        (base / "telegram_offset.txt").write_text(str(off))
    except Exception:
        pass


def load_chats(base: Path) -> dict:
    try:
        return json.loads((base / "telegram_chats.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_chats(base: Path, chats: dict) -> None:
    try:
        (base / "telegram_chats.json").write_text(json.dumps(chats, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# --- adminlar ---
def is_admin(base: Path, chat_id: int, username: str) -> bool:
    s = tg.load_settings(base)
    if chat_id in (s["admin_chat_ids"] or []):
        return True
    wl = {norm(a) for a in (CONTACT.get("admins") or [])}
    return bool(norm(username)) and norm(username) in wl


def ensure_admin(base: Path, chat_id: int, username: str) -> bool:
    """Whitelist dagi yangi chat ID ni saqlaydi. Yangi qo'shilsa True."""
    if not is_admin(base, chat_id, username):
        return False
    s = tg.load_settings(base)
    ids = list(s["admin_chat_ids"] or [])
    if chat_id in ids:
        return False
    f = base / "telegram.json"
    try:
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:
        data = {}
    data["bot_token"] = s["bot_token"]
    data["admin_chat_ids"] = ids + [chat_id]
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def register_chat(base: Path, chat_id: int, frm: dict) -> None:
    chats = load_chats(base)
    key = str(chat_id)
    if key not in chats:
        chats[key] = {
            "username": "@" + (frm.get("username") or "?"),
            "name": f"{frm.get('first_name', '')} {frm.get('last_name', '')}".strip(),
            "first_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_chats(base, chats)


# --- xabarlar ---
def reply(base: Path, chat_id: int, text: str, menu: bool = False) -> bool:
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if menu:
        payload["reply_markup"] = json.dumps(
            {"keyboard": [[{"text": b} for b in row] for row in MENU], "resize_keyboard": True}
        )
    try:
        tg.call_api(base, "sendMessage", payload, timeout=15)
        return True
    except Exception as e:
        log.warning("reply xatosi: %s", e)
        return False


def recent_text(base: Path, n: int = 7) -> str:
    orders = _orders(base)[-n:][::-1]
    if not orders:
        return "Hozircha buyurtmalar yo'q."
    out = ["🧾 <b>So'nggi buyurtmalar:</b>"]
    for o in orders:
        st = "✅" if o.get("status") == "qabul" else "🆕"
        who = f" ({o['accepted_by']})" if o.get("accepted_by") else ""
        out.append(f"{st} <b>#{o['id']}</b>{who} — {_h.escape(o['name'])} • {_fm(o['total'])} so'm")
        out.append(f"   📞 {_h.escape(o.get('phone', ''))}")
    return "\n".join(out)


def today_text(base: Path) -> str:
    t = date.today().isoformat()
    orders = [o for o in _orders(base) if str(o.get("created_at", "")).startswith(t)]
    new = sum(1 for o in orders if o.get("status") != "qabul")
    total = sum(o.get("total", 0) for o in orders)
    return (
        f"📊 <b>Bugungi hisobot ({t}):</b>\n"
        f"🧾 Buyurtmalar: {len(orders)} ta\n"
        f"🆕 Yangi: {new} ta\n"
        f"💰 Summa: {_fm(total)} so'm"
    )


def stock_text(base: Path) -> str:
    out = ["📦 <b>Ombordagi qoldiqlar:</b>"]
    for p in sorted(pstore.get_products(base), key=lambda x: x["stock"]):
        icon = "🔴" if p["stock"] <= 5 else "🟢"
        out.append(f"{icon} {p['stock']} dona — {_h.escape(p['name'])}")
    return "\n".join(out)


def handle_message(base: Path, msg: dict) -> None:
    chat = msg.get("chat", {})
    cid = chat.get("id")
    if not cid:
        return
    frm = msg.get("from", {})
    username = frm.get("username", "")
    text = (msg.get("text") or "").strip()
    register_chat(base, cid, frm)
    if msg.get("photo"):
        if handle_photo(base, cid, msg):
            return
        if handle_check(base, cid, msg):
            return
    if not is_admin(base, cid, username):
        if text.startswith("/start"):
            arg = text.split()[1] if len(text.split()) > 1 else ""
            if arg.startswith("ord_"):
                handle_user_start(base, cid, arg[4:])
                return
        reply(base, cid, "⛔ Bu bot faqat AZA FLOWERS adminlari uchun.\nBuyurtma uchun saytdan foydalaning: azaflowers.uz")
        return
    if ensure_admin(base, cid, username):
        reply(base, cid, "✅ Admin sifatida ulandingiz! Buyurtmalar shu yerga keladi.", menu=True)
        return
    if handle_pending(base, cid, text):
        return
    if text.startswith("/start"):
        arg = text.split()[1] if len(text.split()) > 1 else ""
        if arg.startswith("ord_"):
            handle_user_start(base, cid, arg[4:])
            return
        reply(base, cid, "👋 <b>AZA FLOWERS admin panel</b>\nQuyidagi tugmalardan birini tanlang:", menu=True)
    elif text == "🌷 Mahsulotlar" or text == "/mahsulotlar":
        send_product_list(base, cid)
    elif text == "/add":
        pending[cid] = {"op": "add", "step": "name", "data": {}}
        reply(base, cid, "➕ <b>Yangi gul</b>\n1/7 — Gul nomini yuboring:")
    elif text == "🧾 So'nggi buyurtmalar":
        reply(base, cid, recent_text(base))
    elif text == "📊 Bugungi hisobot":
        reply(base, cid, today_text(base))
    elif text == "📦 Qoldiqlar":
        reply(base, cid, stock_text(base))
    elif text == "🎟 Promokodlar" or text == "/promo_list":
        reply(base, cid, promo_list_text(base))
    elif text == "💳 Karta" or text == "/card":
        reply(base, cid, card_text(base))
    elif text == "/orders":
        send_orders_list(base, cid, "pending", 0)
    elif text == "/stats":
        reply(base, cid, stats_text(base))
    elif text.startswith("/promo_add"):
        reply(base, cid, promo_add_cmd(base, text))
    elif text.startswith("/promo_del"):
        parts = text.split()
        if len(parts) < 2:
            reply(base, cid, "Format: <code>/promo_del KOD</code>")
        else:
            from app import payments as paymod
            ok = paymod.del_promo(base, parts[1])
            reply(base, cid, "✅ O'chirildi." if ok else "❌ Topilmadi.")
    elif text.startswith("/setcard"):
        card = text.replace("/setcard", "").strip().replace(" ", "")
        if len(card) < 12:
            reply(base, cid, "Format: <code>/setcard 8600123456789012</code>")
        else:
            from app import payments as paymod
            paymod.set_payment(base, pay_card=card)
            reply(base, cid, f"✅ Karta saqlandi:\n<code>{_h.escape(card)}</code>")
    elif text in ("ℹ️ Yordam", "/help"):
        reply(base, cid, HELP)
    elif text:
        reply(base, cid, "Tushunmadim 🤔 Menyudan tanlang:", menu=True)


def handle_callback(base: Path, cb: dict) -> None:
    data = cb.get("data", "")
    frm = cb.get("from", {})
    username = "@" + str(frm.get("username") or frm.get("first_name", "?")).lstrip("@")
    qid = cb.get("id")
    msg = cb.get("message") or {}
    cid = (msg.get("chat") or {}).get("id")
    mid = msg.get("message_id")

    def answer(t: str) -> None:
        try:
            tg.call_api(base, "answerCallbackQuery", {"callback_query_id": qid, "text": t}, timeout=10)
        except Exception:
            pass

    if not data.startswith("accept:"):
        answer("Noma'lum buyruq")
        return
    try:
        oid = int(data.split(":")[1])
    except ValueError:
        answer("Xato ID")
        return
    orders = _orders(base)
    o = next((x for x in orders if x.get("id") == oid), None)
    if not o:
        answer("Buyurtma topilmadi")
        return
    if o.get("status") == "qabul":
        answer(f"Allaqachon qabul qilingan ({o.get('accepted_by', '')})")
        return
    o["status"] = "qabul"
    o["accepted_by"] = username
    _save_orders(base, orders)
    if cid and mid:
        new_text = _h.escape(msg.get("text", "")) + f"\n\n✅ <b>Qabul qildi: {_h.escape(username)}</b>"
        try:
            tg.call_api(base, "editMessageText", {
                "chat_id": cid, "message_id": mid, "text": new_text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": []}),
            }, timeout=15)
        except Exception as e:
            log.warning("edit xatosi: %s", e)
    answer("Qabul qilindi ✅")


def dispatch(base: Path, update: dict) -> None:
    if "message" in update:
        handle_message(base, update["message"])
    elif "callback_query" in update:
        cb = update["callback_query"]
        d = cb.get("data", "")
        if d == "plist" or d.startswith("p:") or d.startswith("e:") or d in ("add_new", "add_ok", "add_no") or d.startswith("c:"):
            handle_product_callback(base, cb)
        elif d.startswith("order:") or d.startswith("olist:") or d.startswith("view:") or d in ("stats", "promos", "ocard") or d.startswith("promo_del:"):
            handle_order_callback(base, cb)
        else:
            handle_callback(base, cb)


def run_polling(base: Path) -> None:
    log.info("Telegram bot polling boshlandi")
    while True:
        try:
            off = load_offset(base)
            res = tg.call_api(base, "getUpdates", {"offset": off, "timeout": 20}, timeout=35)
            for u in res.get("result", []):
                save_offset(base, u.get("update_id", off) + 1)
                try:
                    dispatch(base, u)
                except Exception as e:
                    log.warning("update xatosi: %s", e)
        except Exception as e:
            log.warning("polling xatosi: %s", e)
            time.sleep(5)


# --- mahsulotlar (ombor boshqaruvi) ---
pending: dict[int, dict] = {}


def cat_name(slug: str) -> str:
    return next((c["name"] for c in CATEGORIES if c["slug"] == slug), slug)


def product_list_markup(items: list) -> dict:
    kb = []
    for p in items:
        label = p["name"][:28] + ("…" if len(p["name"]) > 28 else "")
        dot = "🔴" if p["stock"] <= 5 else "🟢"
        kb.append([{"text": f"{dot} {label} • {p['stock']}", "callback_data": f"p:{p['slug']}"}])
    kb.append([{"text": "➕ Yangi gul qo'shish", "callback_data": "add_new"}])
    return {"inline_keyboard": kb}


def product_detail_text(p: dict) -> str:
    st = "✅ Faol" if p.get("active", 1) else "⛔ Nofaol"
    old = f" (eski: {_fm(p['old_price'])})" if p.get("old_price") else ""
    return (
        f"🌷 <b>{_h.escape(p['name'])}</b>\n📁 {cat_name(p['category'])} • {st}\n"
        f"💰 {_fm(p['price'])} so'm{old}\n📦 Qoldiq: {p['stock']} dona\n\n"
        f"{_h.escape(p.get('description', ''))}"
    )


def detail_markup(p: dict) -> dict:
    slug = p["slug"]
    tog = "⛔ Nofaol qilish" if p.get("active", 1) else "✅ Faol qilish"
    return {"inline_keyboard": [
        [{"text": "💰 Narx", "callback_data": f"e:price:{slug}"},
         {"text": "📦 Qoldiq", "callback_data": f"e:stock:{slug}"}],
        [{"text": "✏️ Tavsif", "callback_data": f"e:desc:{slug}"},
         {"text": "🖼 Rasm", "callback_data": f"e:photo:{slug}"}],
        [{"text": tog, "callback_data": f"e:toggle:{slug}"}],
        [{"text": "« Mahsulotlar", "callback_data": "plist"}]]}


def send_product_list(base: Path, cid: int) -> None:
    items = pstore.get_products(base)
    try:
        tg.call_api(base, "sendMessage", {
            "chat_id": cid,
            "text": f"🌷 <b>Mahsulotlar ({len(items)} ta)</b>\nTahrirlash uchun tanlang:",
            "parse_mode": "HTML",
            "reply_markup": json.dumps(product_list_markup(items))}, timeout=15)
    except Exception as e:
        log.warning("plist xatosi: %s", e)


def edit_to(base: Path, cid: int, mid: int, text: str, markup: dict) -> bool:
    try:
        tg.call_api(base, "editMessageText", {
            "chat_id": cid, "message_id": mid, "text": text,
            "parse_mode": "HTML", "reply_markup": json.dumps(markup)}, timeout=15)
        return True
    except Exception as e:
        log.warning("edit xatosi: %s", e)
        return False


def _parse_money(text: str):
    try:
        v = int(text.replace(" ", "").replace(",", ""))
        return v if v > 0 else None
    except ValueError:
        return None


def handle_product_callback(base: Path, cb: dict) -> None:
    data = cb.get("data", "")
    msg = cb.get("message") or {}
    cid = (msg.get("chat") or {}).get("id")
    mid = msg.get("message_id")
    qid = cb.get("id")

    def answer(t: str) -> None:
        try:
            tg.call_api(base, "answerCallbackQuery", {"callback_query_id": qid, "text": t}, timeout=10)
        except Exception:
            pass

    parts = data.split(":")
    if data == "plist":
        items = pstore.get_products(base)
        edit_to(base, cid, mid, f"🌷 <b>Mahsulotlar ({len(items)} ta)</b>\nTahrirlash uchun tanlang:",
                product_list_markup(items))
        answer("Ro'yxat")
    elif parts[0] == "p" and len(parts) == 2:
        p = pstore.get_product(base, parts[1])
        if not p:
            answer("Topilmadi")
            return
        edit_to(base, cid, mid, product_detail_text(p), detail_markup(p))
        answer(p["name"][:40])
    elif parts[0] == "e" and len(parts) == 3:
        _, field, slug = parts
        p = pstore.get_product(base, slug)
        if not p:
            answer("Topilmadi")
            return
        if field == "toggle":
            pstore.upsert_field(base, slug, "active", 0 if p.get("active", 1) else 1)
            p = pstore.get_product(base, slug)
            edit_to(base, cid, mid, product_detail_text(p), detail_markup(p))
            answer("O'zgartirildi")
        else:
            pending[cid] = {"op": "set_" + field, "slug": slug}
            prompts = {"price": "💰 Yangi narxni so'mda yuboring:",
                       "stock": "📦 Yangi qoldiq sonini yuboring:",
                       "desc": "✏️ Yangi tavsifni yuboring:",
                       "photo": "🖼 Gul rasmini foto ko'rinishida yuboring:"}
            reply(base, cid, prompts.get(field, "Qiymatni yuboring:"))
            answer("Kuting...")
    elif data == "add_new":
        pending[cid] = {"op": "add", "step": "name", "data": {}}
        reply(base, cid, "➕ <b>Yangi gul</b>\n1/7 — Gul nomini yuboring:")
        answer("Boshladik")
    elif parts[0] == "c" and len(parts) == 2:
        st = pending.get(cid)
        if not st or st.get("op") != "add" or st.get("step") != "cat":
            answer("Avval /add bilan boshlang")
            return
        if parts[1] not in [c["slug"] for c in CATEGORIES]:
            answer("Noto'g'ri kategoriya")
            return
        st["data"]["category"] = parts[1]
        st["step"] = "price"
        reply(base, cid, "3/7 — Narxni so'mda yuboring (masalan: 450000):")
        answer(cat_name(parts[1]))
    elif data in ("add_ok", "add_no"):
        st = pending.pop(cid, None)
        if not st or st.get("op") != "add":
            answer("Bekor qilindi")
            return
        if data == "add_no":
            reply(base, cid, "❌ Bekor qilindi.")
        else:
            p = pstore.add_product(base, st["data"])
            reply(base, cid, f"✅ Saqlandi!\n\n{product_detail_text(p)}")
        answer("Tayyor")


def handle_pending(base: Path, cid: int, text: str) -> bool:
    """Pending holat bo'lsa qayta ishlaydi. True = xabar iste'mol qilindi."""
    st = pending.get(cid)
    if not st:
        return False
    if text.startswith("/"):
        pending.pop(cid, None)
        return False
    op = st["op"]
    if op == "set_price":
        v = _parse_money(text)
        if v is None:
            reply(base, cid, "❌ Narx noto'g'ri. Faqat raqam yuboring:")
            return True
        try:
            p = pstore.upsert_field(base, st["slug"], "price", v)
        except KeyError:
            pending.pop(cid, None)
            reply(base, cid, "Mahsulot topilmadi.")
            return True
        pending.pop(cid, None)
        reply(base, cid, f"✅ Narx yangilandi!\n\n{product_detail_text(p)}")
        return True
    if op == "set_stock":
        try:
            v = int(text.replace(" ", ""))
            assert v >= 0
        except (ValueError, AssertionError):
            reply(base, cid, "❌ Son noto'g'ri. Masalan: 10")
            return True
        try:
            p = pstore.upsert_field(base, st["slug"], "stock", v)
        except KeyError:
            pending.pop(cid, None)
            reply(base, cid, "Mahsulot topilmadi.")
            return True
        pending.pop(cid, None)
        reply(base, cid, f"✅ Qoldiq yangilandi!\n\n{product_detail_text(p)}")
        return True
    if op == "set_desc":
        if len(text) < 5:
            reply(base, cid, "❌ Tavsif juda qisqa.")
            return True
        try:
            p = pstore.upsert_field(base, st["slug"], "description", text[:500])
        except KeyError:
            pending.pop(cid, None)
            reply(base, cid, "Mahsulot topilmadi.")
            return True
        pending.pop(cid, None)
        reply(base, cid, f"✅ Tavsif yangilandi!\n\n{product_detail_text(p)}")
        return True
    if op == "set_photo":
        reply(base, cid, "🖼 Rasmni foto ko'rinishida yuboring (fayl ko'rinishida emas):")
        return True
    if op == "add":
        return handle_add_step(base, cid, text, st)
    pending.pop(cid, None)
    return False


def handle_add_step(base: Path, cid: int, text: str, st: dict) -> bool:
    d = st["data"]
    step = st["step"]
    if step == "name":
        if len(text) < 3:
            reply(base, cid, "❌ Nom juda qisqa. Qayta yuboring:")
            return True
        d["name"] = text[:80]
        st["step"] = "cat"
        kb = {"inline_keyboard": [
            [{"text": c["name"], "callback_data": f"c:{c['slug']}"} for c in CATEGORIES[i:i + 2]]
            for i in range(0, len(CATEGORIES), 2)]}
        try:
            tg.call_api(base, "sendMessage", {
                "chat_id": cid, "text": "2/7 — Kategoriyani tanlang:",
                "parse_mode": "HTML", "reply_markup": json.dumps(kb)}, timeout=15)
        except Exception as e:
            log.warning("cat xatosi: %s", e)
        return True
    if step == "price":
        v = _parse_money(text)
        if v is None:
            reply(base, cid, "❌ Narx noto'g'ri. Masalan: 450000")
            return True
        d["price"] = v
        d["old_price"] = None
        st["step"] = "old"
        reply(base, cid, "4/7 — Eski narx (chegirma uchun)? Yo'q bo'lsa 0 yuboring:")
        return True
    if step == "old":
        v = _parse_money(text) or 0
        d["old_price"] = v if v and v > d["price"] else None
        st["step"] = "stock"
        reply(base, cid, "5/7 — Qoldiq soni? Masalan: 10")
        return True
    if step == "stock":
        try:
            v = int(text.replace(" ", ""))
            assert v >= 0
        except (ValueError, AssertionError):
            reply(base, cid, "❌ Son noto'g'ri. Masalan: 10")
            return True
        d["stock"] = v
        st["step"] = "desc"
        reply(base, cid, "6/7 — Tavsifni yuboring:")
        return True
    if step == "desc":
        if len(text) < 5:
            reply(base, cid, "❌ Tavsif juda qisqa.")
            return True
        d["description"] = text[:500]
        d["is_featured"] = 0
        d["img"] = dict(pstore.IMG_DEFAULTS.get(d["category"], pstore.IMG_DEFAULTS["buketlar"]))
        st["step"] = "photo"
        reply(base, cid, "7/7 — Gul rasmini foto ko'rinishida yuboring (yoki 'o'tkazish' deb yozing):")
        return True
    if step == "photo":
        if text.lower() in ("skip", "o'tkazish", "o'tkazib yuborish", "0", "-", "yo'q"):
            send_add_confirm(base, cid, d)
            st["step"] = "confirm"
            return True
        reply(base, cid, "🖼 Rasmni foto ko'rinishida yuboring yoki 'o'tkazish' deb yozing:")
        return True
    pending.pop(cid, None)
    return False


def send_add_confirm(base: Path, cid: int, d: dict) -> None:
    kb = {"inline_keyboard": [[
        {"text": "✅ Saqlash", "callback_data": "add_ok"},
        {"text": "❌ Bekor", "callback_data": "add_no"}]]}
    photo_line = "\n🖼 Rasm biriktirilgan" if d.get("photo") else ""
    try:
        tg.call_api(base, "sendMessage", {
            "chat_id": cid,
            "text": f"Tekshiring:\n\n<b>{_h.escape(d['name'])}</b>\n"
                    f"📁 {cat_name(d['category'])}\n💰 {_fm(d['price'])} so'm\n"
                    f"📦 {d['stock']} dona{photo_line}\n\n{_h.escape(d['description'])}",
            "parse_mode": "HTML", "reply_markup": json.dumps(kb)}, timeout=15)
    except Exception as e:
        log.warning("confirm xatosi: %s", e)


def handle_photo(base: Path, cid: int, msg: dict) -> bool:
    """Foto-xabarni qayta ishlaydi. True = iste'mol qilindi."""
    st = pending.get(cid)
    if not st:
        return False
    photos = msg.get("photo") or []
    if not photos:
        return False
    file_id = photos[-1].get("file_id")
    op = st.get("op")
    if op == "set_photo":
        try:
            path = tg.download_photo(base, file_id, st.get("slug"))
            p = pstore.upsert_field(base, st.get("slug"), "photo", path)
        except Exception as e:
            log.warning("rasm xatosi: %s", e)
            reply(base, cid, "❌ Rasmni saqlab bo'lmadi. Boshqa rasm yuboring:")
            return True
        pending.pop(cid, None)
        reply(base, cid, f"✅ Rasm yangilandi!\n\n{product_detail_text(p)}")
        return True
    if op == "add" and st.get("step") == "photo":
        try:
            d = st["data"]
            path = tg.download_photo(base, file_id, pstore.slugify(d["name"]))
            d["photo"] = path
        except Exception as e:
            log.warning("rasm xatosi: %s", e)
            reply(base, cid, "❌ Rasmni saqlab bo'lmadi. Boshqa rasm yuboring yoki 'o'tkazish' deb yozing:")
            return True
        send_add_confirm(base, cid, st["data"])
        st["step"] = "confirm"
        return True
    return False


# --- buyurtma statuslari (SAMA uslubida) ---
STATUS = {
    "yangi": "🆕 Yangi",
    "qabul": "✅ Qabul qilindi",
    "awaiting_payment": "⏳ To'lov kutilmoqda",
    "awaiting_confirm": "🔎 Chek tekshirilmoqda",
    "accepted": "✅ Qabul qilindi",
    "preparing": "🟡 Tayyorlanmoqda",
    "delivering": "🚚 Yo'lda",
    "delivered": "🏁 Yetkazildi",
    "closed": "🎉 Yakunlandi",
    "cancelled": "❌ Bekor qilindi",
    "rejected": "⛔ Rad etildi",
}

FILTERS = {
    "pending": ("Kutilmoqda", ["yangi", "awaiting_payment", "awaiting_confirm"]),
    "accepted": ("Qabul qilingan", ["qabul", "accepted", "preparing", "delivering", "delivered", "closed"]),
    "rejected": ("Rad etilgan", ["cancelled", "rejected"]),
    "all": ("Barchasi", None),
}
PAGE_SIZE = 5

USER_NOTIFY = {
    "accepted": "✅ To'lovingiz tasdiqlandi! Buyurtmangiz tayyorlanmoqda 🌷",
    "rejected": "❌ Buyurtmangiz rad etildi. Chekda muammo bo'lsa, qayta yuboring.",
    "preparing": "🟡 Buyurtmangiz tayyorlanmoqda 🌷",
    "delivering": "🚚 Buyurtmangiz yo'lda! Kuryer tez orada yetkazadi.",
    "delivered": "📦 Buyurtma yetkazildi! Qabul qilganingizni tasdiqlang 👇",
    "cancelled": "❌ Buyurtmangiz bekor qilindi.",
}


def st_label(s: str) -> str:
    return STATUS.get(s, s)


def order_keyboard(o: dict):
    st = o.get("status", "yangi")
    oid = o["id"]
    if st in ("delivered", "closed", "cancelled", "rejected"):
        return None
    if st == "awaiting_confirm":
        return {"inline_keyboard": [
            [{"text": "✅ Chekni tasdiqlash", "callback_data": f"order:{oid}:accepted"},
             {"text": "❌ Rad etish", "callback_data": f"order:{oid}:rejected"}],
            [{"text": "📋 Ro'yxat", "callback_data": "olist:pending:0"}]]}
    if st in ("yangi",):
        return {"inline_keyboard": [
            [{"text": "✅ Qabul qilish", "callback_data": f"order:{oid}:accepted"},
             {"text": "❌ Rad etish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "olist:pending:0"}]]}
    if st == "awaiting_payment":
        return {"inline_keyboard": [
            [{"text": "❌ Bekor qilish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "olist:pending:0"}]]}
    return {"inline_keyboard": [
        [{"text": "🟡 Tayyorlanmoqda", "callback_data": f"order:{oid}:preparing"},
         {"text": "🚚 Yo'lda", "callback_data": f"order:{oid}:delivering"}],
        [{"text": "🏁 Yetkazildi", "callback_data": f"order:{oid}:delivered"},
         {"text": "❌ Bekor", "callback_data": f"order:{oid}:cancelled"}],
        [{"text": "📋 Ro'yxat", "callback_data": "olist:pending:0"}]]}


def refresh_order_msgs(base: Path, o: dict) -> None:
    from app.telegram import order_text as _ot
    kb = order_keyboard(o)
    for m in o.get("msgs", []) or []:
        try:
            tg.call_api(base, "editMessageText", {
                "chat_id": m["chat"], "message_id": m["msg"],
                "text": f"{_ot(o)}\n\nHolati: {st_label(o.get('status', ''))}",
                "parse_mode": "HTML",
                **({"reply_markup": json.dumps(kb)} if kb else {}),
            }, timeout=15)
        except Exception as e:
            log.warning("refresh xatosi: %s", e)


def set_status(base: Path, oid: int, status: str, by: str = "") -> dict | None:
    orders = _orders(base)
    o = next((x for x in orders if x.get("id") == oid), None)
    if not o:
        return None
    o["status"] = status
    if by:
        o["accepted_by"] = by
    _save_orders(base, orders)
    refresh_order_msgs(base, o)
    if o.get("tg_user") and status in USER_NOTIFY:
        try:
            payload: dict = {"chat_id": o["tg_user"], "text": f"📦 Buyurtma {o.get('no', '')}\n{USER_NOTIFY[status]}"}
            if status == "delivered":
                payload["reply_markup"] = json.dumps({"inline_keyboard": [[
                    {"text": "✅ Qabul qildim", "callback_data": f"recv:{oid}"}]]})
            tg.call_api(base, "sendMessage", payload, timeout=15)
        except Exception as e:
            log.warning("user notify xatosi: %s", e)
    return o


def filtered_orders(base: Path, filt: str) -> list:
    name, statuses = FILTERS.get(filt, FILTERS["pending"])
    orders = _orders(base)[::-1]
    if statuses is None:
        return orders
    return [o for o in orders if o.get("status", "yangi") in statuses]


def orders_list_markup(filt: str, page: int, total_pages: int) -> dict:
    kb = [[{"text": n, "callback_data": f"olist:{f}:0"}] for f, (n, _) in
          [("pending", FILTERS["pending"]), ("accepted", FILTERS["accepted"]),
           ("rejected", FILTERS["rejected"]), ("all", FILTERS["all"])]]
    nav = []
    if page > 0:
        nav.append({"text": "◀", "callback_data": f"olist:{filt}:{page - 1}"})
    if page < total_pages - 1:
        nav.append({"text": "▶", "callback_data": f"olist:{filt}:{page + 1}"})
    if nav:
        kb.append(nav)
    return {"inline_keyboard": kb}


def send_orders_list(base: Path, cid: int, filt: str = "pending", page: int = 0, edit_mid: int = 0) -> None:
    orders = filtered_orders(base, filt)
    pages = max(1, (len(orders) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    chunk = orders[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    name = FILTERS.get(filt, FILTERS["pending"])[0]
    out = [f"🧾 <b>Buyurtmalar — {name}</b> ({len(orders)} ta, {page + 1}/{pages})"]
    kb_rows = []
    for o in chunk:
        out.append(f"{st_label(o.get('status', ''))} <b>#{o['id']}</b> — {_h.escape(o.get('name', ''))} • {_fm(o.get('total', 0))} so'm")
        kb_rows.append([{"text": f"#{o['id']} — {o.get('name', '')[:20]}", "callback_data": f"view:{o['id']}"}])
    if not chunk:
        out.append("Bo'sh.")
    kb = orders_list_markup(filt, page, pages)
    kb["inline_keyboard"] = kb_rows + kb["inline_keyboard"]
    if edit_mid:
        edit_to(base, cid, edit_mid, "\n".join(out), kb)
    else:
        try:
            tg.call_api(base, "sendMessage", {"chat_id": cid, "text": "\n".join(out),
                "parse_mode": "HTML", "reply_markup": json.dumps(kb)}, timeout=15)
        except Exception as e:
            log.warning("olist xatosi: %s", e)


def stats_text(base: Path) -> str:
    orders = _orders(base)
    t = date.today().isoformat()
    today = [o for o in orders if str(o.get("created_at", "")).startswith(t)]
    by_st: dict[str, int] = {}
    for o in orders:
        by_st[o.get("status", "yangi")] = by_st.get(o.get("status", "yangi"), 0) + 1
    total = sum(o.get("total", 0) for o in orders if o.get("status") not in ("cancelled", "rejected"))
    out = ["📊 <b>Statistika</b>", f"🧾 Jami: {len(orders)} ta • 💰 { _fm(total)} so'm",
           f"📅 Bugun: {len(today)} ta"]
    for s, n in by_st.items():
        out.append(f"{st_label(s)}: {n}")
    from app import payments as paymod
    promos = paymod.list_promos(base)
    out.append(f"🎟 Promokodlar: {len(promos)} ta")
    return "\n".join(out)


def promo_list_text(base: Path) -> str:
    from app import payments as paymod
    promos = paymod.list_promos(base)
    if not promos:
        return "🎟 Promokodlar yo'q.\nQo'shish: <code>/promo_add NAVROZ10 10 50</code>"
    out = ["🎟 <b>Promokodlar:</b>"]
    for code, p in promos.items():
        uses = f"{p.get('used', 0)}/{p.get('max_uses') or '∞'}"
        on = "✅" if p.get("active", 1) else "⛔"
        out.append(f"{on} <code>{_h.escape(code)}</code> — {p.get('pct')}% • {uses}")
    out.append("\nO'chirish: <code>/promo_del KOD</code>")
    return "\n".join(out)


def promo_add_cmd(base: Path, text: str) -> str:
    parts = text.split()
    if len(parts) < 3:
        return "Format: <code>/promo_add KOD FOIZ [SONI]</code>\nMasalan: <code>/promo_add NAVROZ10 10 50</code>"
    try:
        from app import payments as paymod
        mx = int(parts[3]) if len(parts) > 3 else 0
        p = paymod.add_promo(base, parts[1], int(parts[2]), mx)
        return f"✅ Saqlandi: <code>{_h.escape(p['code'])}</code> — {p['pct']}%"
    except (ValueError, IndexError) as e:
        return f"❌ {e}"


def card_text(base: Path) -> str:
    from app import payments as paymod
    pay = paymod.get_payment(base)
    card = pay.get("pay_card") or "—"
    return (f"💳 <b>To'lov kartasi:</b>\n<code>{_h.escape(card)}</code>\n"
            f"Oldindan to'lov: {pay.get('prepay_pct', 50)}%\n\n"
            "O'zgartirish: <code>/setcard 8600123456789012</code>")


def payment_instructions(base: Path, o: dict) -> str:
    from app import payments as paymod
    card = paymod.get_payment(base).get("pay_card", "")
    card_block = f"<code>{_h.escape(card)}</code>" if card else "Karta raqamini operatorimiz yuboradi."
    return (
        f"🧾 Buyurtma {o.get('no', '')}\n"
        f"💰 Jami: {_fm(o.get('total', 0))} so'm\n"
        f"💳 Oldindan ({paymod.get_payment(base).get('prepay_pct', 50)}%): <code>{_fm(o.get('prepay', 0))}</code>\n\n"
        f"⛔️ MUHIM: Aynan {_fm(o.get('prepay', 0))} to'lang — ko'p ham, kam ham emas.\n\n"
        f"💳 Karta:\n{card_block}\n\n"
        "1-qadam: To'lovni qiling\n"
        "2-qadam: Chekni shu yerga rasm qilib yuboring 📸"
    )


def user_status_text(o: dict) -> str:
    return f"📦 Buyurtma {o.get('no', '')}\n{st_label(o.get('status', ''))}\n💰 Jami: {_fm(o.get('total', 0))} so'm"


def handle_user_start(base: Path, cid: int, oid_raw: str) -> None:
    try:
        oid = int(oid_raw)
    except ValueError:
        reply(base, cid, "👋 AZA FLOWERS 🌷\nBuyurtma uchun saytdan foydalaning: azaflowers.uz")
        return
    orders = _orders(base)
    o = next((x for x in orders if x.get("id") == oid), None)
    if not o:
        reply(base, cid, "❌ Buyurtma topilmadi.")
        return
    o["tg_user"] = cid
    _save_orders(base, orders)
    if o.get("status") == "awaiting_payment":
        reply(base, cid, payment_instructions(base, o))
    else:
        reply(base, cid, user_status_text(o))


def handle_check(base: Path, cid: int, msg: dict) -> bool:
    """Mijoz chek rasmini yuborsa — adminlarga forward + awaiting_confirm."""
    if pending.get(cid):
        return False
    try:
        if is_admin(base, cid, (msg.get("from") or {}).get("username", "")):
            return False
    except Exception:
        pass
    photos = msg.get("photo") or []
    if not photos:
        return False
    orders = _orders(base)
    o = next((x for x in orders[::-1]
              if x.get("tg_user") == cid and x.get("status") == "awaiting_payment"), None)
    if not o:
        return False
    file_id = photos[-1].get("file_id")
    o["check_file"] = file_id
    o["status"] = "awaiting_confirm"
    _save_orders(base, orders)
    refresh_order_msgs(base, o)
    s = tg.load_settings(base)
    for admin in s["admin_chat_ids"] or []:
        try:
            tg.call_api(base, "forwardMessage", {
                "chat_id": admin, "from_chat_id": cid,
                "message_id": msg.get("message_id")}, timeout=15)
        except Exception as e:
            log.warning("forward xatosi: %s", e)
    from app.telegram import order_text as _ot
    kb = order_keyboard(o)
    sent = []
    for admin in s["admin_chat_ids"] or []:
        try:
            r = tg.call_api(base, "sendMessage", {"chat_id": admin,
                "text": f"📸 <b>Yangi chek!</b>\n\n{_ot(o)}",
                "parse_mode": "HTML",
                **({"reply_markup": json.dumps(kb)} if kb else {})}, timeout=15)
            if r.get("ok"):
                sent.append({"chat": admin, "msg": r["result"]["message_id"]})
        except Exception as e:
            log.warning("check notify xatosi: %s", e)
    if sent:
        orders = _orders(base)
        oo = next((x for x in orders if x.get("id") == o["id"]), None)
        if oo:
            oo["msgs"] = (oo.get("msgs") or []) + sent
            oo["notified"] = 1
            _save_orders(base, orders)
    reply(base, cid, "✅ Chek qabul qilindi!\n🔎 Admin tekshirmoqda, kuting...")
    return True


def handle_order_callback(base: Path, cb: dict) -> None:
    data = cb.get("data", "")
    msg = cb.get("message") or {}
    cid = (msg.get("chat") or {}).get("id")
    mid = msg.get("message_id")
    qid = cb.get("id")
    frm = cb.get("from", {})

    def answer(t: str) -> None:
        try:
            tg.call_api(base, "answerCallbackQuery", {"callback_query_id": qid, "text": t}, timeout=10)
        except Exception:
            pass

    if data.startswith("recv:"):
        try:
            oid = int(data.split(":")[1])
        except ValueError:
            answer("Xato")
            return
        orders = _orders(base)
        o = next((x for x in orders if x.get("id") == oid), None)
        if not o or o.get("tg_user") != frm.get("id") or o.get("status") != "delivered":
            answer("Mumkin emas")
            return
        o["status"] = "closed"
        _save_orders(base, orders)
        refresh_order_msgs(base, o)
        answer("Rahmat! 🎉")
        return

    if not is_admin(base, cid, frm.get("username", "")):
        answer("⛔ Faqat adminlar")
        return

    if data.startswith("order:"):
        parts = data.split(":")
        if len(parts) != 3:
            answer("Xato")
            return
        try:
            oid = int(parts[1])
        except ValueError:
            answer("Xato ID")
            return
        username = "@" + str(frm.get("username") or frm.get("first_name", "?")).lstrip("@")
        o = set_status(base, oid, parts[2], username)
        if not o:
            answer("Topilmadi")
            return
        answer(st_label(parts[2]))
    elif data.startswith("olist:"):
        parts = data.split(":")
        filt = parts[1] if len(parts) > 1 else "pending"
        try:
            page = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            page = 0
        send_orders_list(base, cid, filt, page, edit_mid=mid or 0)
        answer("Ro'yxat")
    elif data.startswith("view:"):
        try:
            oid = int(data.split(":")[1])
        except ValueError:
            answer("Xato")
            return
        o = next((x for x in _orders(base) if x.get("id") == oid), None)
        if not o:
            answer("Topilmadi")
            return
        from app.telegram import order_text as _ot
        kb = order_keyboard(o) or {"inline_keyboard": [[
            {"text": "📋 Ro'yxat", "callback_data": "olist:pending:0"}]]}
        edit_to(base, cid, mid, f"{_ot(o)}\n\nHolati: {st_label(o.get('status', ''))}", kb)
        answer(f"#{oid}")
    elif data == "stats":
        reply(base, cid, stats_text(base))
        answer("Statistika")
    elif data == "promos":
        reply(base, cid, promo_list_text(base))
        answer("Promo")
    elif data == "ocard":
        reply(base, cid, card_text(base))
        answer("Karta")
    elif data.startswith("promo_del:"):
        from app import payments as paymod
        ok = paymod.del_promo(base, data.split(":", 1)[1])
        answer("O'chirildi" if ok else "Topilmadi")
        if ok:
            reply(base, cid, promo_list_text(base))
    else:
        answer("Noma'lum buyruq")
