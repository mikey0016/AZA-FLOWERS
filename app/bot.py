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

HELP = (
    "ℹ️ Yangi buyurtma kelganda tugmalar bilan xabar keladi:\n"
    "✅ Qabul — mijozga qo'ng'iroq qiling\n"
    "🟡 → 🚚 → 🏁 — holatni yangilang\n"
    "❌ — bekor qilingan\n\n"
    "➕ Mahsulot qo'shish: /addproduct\n"
    "📦 Mahsulotlar: /products · o'chirish: /delproduct SLUG\n"
    "🎟 Promokod: /promo_add KOD FOIZ [SONI]\n"
    "💳 Karta: /setcard KARTA"
)

USER_HELP = (
    "🌷 <b>AZA FLOWERS</b> do'kon boti.\n\n"
    "Buyurtma berish uchun saytdan buyurtma qoldiring — to'lov uchun shu botga link beriladi.\n\n"
    "/myorders — buyurtmalarim"
)


def _fm(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def pretty_card(card: str) -> str:
    d = "".join(ch for ch in str(card or "") if ch.isdigit())
    return " ".join(d[i:i + 4] for i in range(0, len(d), 4)) or str(card or "")


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


# Reply-klaviatura olib tashlangan (SAMA uslubi — faqat inline tugmalar).
# menu=True endi mijozdagi eski klaviaturani yashiradi.
def reply(base: Path, chat_id: int, text: str, menu: bool = False) -> bool:
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if menu:
        payload["reply_markup"] = json.dumps({"remove_keyboard": True})
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
            reply(base, cid, "👋 <b>AZA FLOWERS</b> do'kon boti.\n\nBuyurtma berish uchun saytdan buyurtma qoldiring — to'lov uchun shu botga link beriladi.\n\n/myorders — buyurtmalarim")
            return
        if text.startswith("/myorders"):
            send_myorders(base, cid)
            return
        if text.startswith("/help"):
            reply(base, cid, USER_HELP)
            return
        reply(base, cid, "ℹ️ Buyurtma uchun saytdan foydalaning.\n/myorders — buyurtmalarim")
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
        reply(base, cid, "👋 <b>AZA FLOWERS — admin panel</b>\n━━━━━━━━━━━━\n<b>Buyruqlar</b>\n\n📋 /orders — <i>so'nggi buyurtmalar</i>\n📊 /stats — <i>statistika</i>\n➕ /addproduct — <i>yangi mahsulot</i>\n📦 /products — <i>mahsulotlar ro'yxati</i>\n🎟 /promo_add KOD FOIZ [SONI] — <i>promokod</i>\n💳 /setcard KARTA — <i>to'lov kartasi</i>\nℹ️ /help — <i>yordam</i>", menu=True)
        send_panel(base, cid)
        return
    elif text == "🌷 Mahsulotlar" or text in ("/mahsulotlar", "/products"):
        send_product_list(base, cid)
    elif text in ("/add", "/addproduct", "/mahsulot"):
        add_start(base, cid)
    elif text == "🧾 So'nggi buyurtmalar":
        reply(base, cid, recent_text(base))
    elif text == "📊 Bugungi hisobot":
        reply(base, cid, today_text(base))
    elif text == "📦 Qoldiqlar":
        reply(base, cid, stock_text(base))
    elif text == "🎟 Promokodlar" or text == "/promo_list":
        send_promos(base, cid)
    elif text == "💳 Karta" or text == "/card":
        reply(base, cid, card_text(base))
    elif text == "/panel":
        send_panel(base, cid)
    elif text.startswith("/myorders"):
        send_myorders(base, cid)
    elif text in ("/cancel", "/bekor"):
        if pending.pop(cid, None):
            reply(base, cid, "❌ Bekor qilindi.")
        else:
            reply(base, cid, "Bekor qilinadigan amal yo'q.")
    elif text.startswith("/delproduct") or text.startswith("/mahsulot_del"):
        parts = text.split()
        if len(parts) < 2:
            reply(base, cid, "♻️ Format: <code>/delproduct SLUG</code> (SLUG ni /products dan ko'ring)")
        else:
            ok = pstore.del_product(base, parts[1].strip())
            reply(base, cid, "🗑 O'chirildi." if ok else "⛔ Topilmadi.")
    elif text == "/orders":
        send_orders_list(base, cid, "pending", 0)
    elif text == "/stats":
        reply(base, cid, stats_text(base))
    elif text.startswith("/promo_add"):
        reply(base, cid, promo_add_cmd(base, text))
    elif text.startswith("/promo_del"):
        parts = text.split()
        if len(parts) < 2:
            reply(base, cid, "♻️ Format: <code>/promo_del KOD</code>")
        else:
            from app import payments as paymod
            ok = paymod.del_promo(base, parts[1])
            reply(base, cid, "🗑 O'chirildi." if ok else "⛔ Topilmadi.")
    elif text.startswith("/setcard"):
        parts = text.split()
        if len(parts) < 2:
            reply(base, cid, "♻️ Format: <code>/setcard 8600123456789012</code>")
        else:
            from app import payments as paymod
            paymod.set_payment(base, pay_card=parts[1])
            reply(base, cid, f"💳 To'lov kartasi saqlandi: <code>{_h.escape(parts[1])}</code>")
    elif text in ("ℹ️ Yordam", "/help"):
        reply(base, cid, HELP)
    elif text:
        reply(base, cid, "Noma'lum buyruq. /help ni bosing.", menu=True)


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
        if d.startswith("padd:"):
            handle_padd_callback(base, cb)
        elif d == "plist" or d.startswith("p:") or d.startswith("pdel:") or d.startswith("f:") or d.startswith("e:") or d in ("add_new", "add_ok", "add_no") or d.startswith("c:"):
            handle_product_callback(base, cb)
        elif d.startswith("order:") or d.startswith("olist:") or d.startswith("view:") or d.startswith("panel:") or d in ("stats", "promos", "ocard") or d.startswith("promo_del:") or d.startswith("recv:"):
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
        label = p["name"][:24] + ("…" if len(p["name"]) > 24 else "")
        dot = "🔴" if p["stock"] <= 5 else "🟢"
        kb.append([{"text": f"{dot} {label} • {p['stock']}", "callback_data": f"p:{p['slug']}"},
                   {"text": "🗑", "callback_data": f"pdel:{p['slug']}"}])
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
    feat = int(p.get("is_featured", 0) or 0)
    feat_row = [
        {"text": ("● " if feat == 0 else "○ ") + "Oddiy", "callback_data": f"f:{slug}:0"},
        {"text": ("● " if feat == 1 else "○ ") + "TOP", "callback_data": f"f:{slug}:1"},
        {"text": ("● " if feat == 2 else "○ ") + "YANGI", "callback_data": f"f:{slug}:2"},
    ]
    return {"inline_keyboard": [
        [{"text": "💰 Narx", "callback_data": f"e:price:{slug}"},
         {"text": "📦 Qoldiq", "callback_data": f"e:stock:{slug}"}],
        [{"text": "💲 Eski narx", "callback_data": f"e:old:{slug}"},
         {"text": "✏️ Tavsif", "callback_data": f"e:desc:{slug}"}],
        [{"text": "🖼 Rasm", "callback_data": f"e:photo:{slug}"},
         {"text": tog, "callback_data": f"e:toggle:{slug}"}],
        feat_row,
        [{"text": "🗑 O'chirish", "callback_data": f"pdel:{slug}"}],
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
        sent_photo = False
        if p.get("photo"):
            try:
                tg.send_photo(base, cid, p["photo"], product_detail_text(p), detail_markup(p))
                sent_photo = True
            except Exception as e:
                log.warning("foto yuborilmadi: %s", e)
        if not sent_photo:
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
                       "old": "💲 Eski narxni so'mda yuboring (chegirma bo'lmasa 0):",
                       "stock": "📦 Yangi qoldiq sonini yuboring:",
                       "desc": "✏️ Yangi tavsifni yuboring:",
                       "photo": "🖼 Gul rasmini foto ko'rinishida yoki rasm havolasi (https://...) yuboring:"}
            reply(base, cid, prompts.get(field, "Qiymatni yuboring:"))
            answer("Kuting...")
    elif data == "add_new":
        add_start(base, cid)
        answer("Boshladik")
    elif parts[0] == "pdel" and len(parts) == 2:
        ok = pstore.del_product(base, parts[1])
        if not ok:
            answer("Topilmadi")
            return
        items = pstore.get_products(base)
        edit_to(base, cid, mid, f"🗑 O'chirildi.\n\n🌷 <b>Mahsulotlar ({len(items)} ta)</b>\nTahrirlash uchun tanlang:",
                product_list_markup(items))
        answer("O'chirildi")
    elif parts[0] == "f" and len(parts) == 3:
        try:
            v = int(parts[2])
            assert v in (0, 1, 2)
        except (ValueError, AssertionError):
            answer("Xato")
            return
        try:
            pstore.upsert_field(base, parts[1], "is_featured", v)
        except KeyError:
            answer("Topilmadi")
            return
        p = pstore.get_product(base, parts[1])
        edit_to(base, cid, mid, product_detail_text(p), detail_markup(p))
        answer(["Oddiy", "TOP", "YANGI"][v])
    elif parts[0] == "c" and len(parts) == 2:
        add_pick_cat(base, cid, parts[1], answer)
    elif data in ("add_ok", "add_no"):
        if data == "add_no":
            add_cancel(base, cid)
        else:
            add_save(base, cid)
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
    if op == "set_old":
        v = _parse_money(text) or 0
        try:
            cur = pstore.get_product(base, st["slug"]) or {}
            price = (cur.get("price") or 0)
            new_old = v if v and v > price else None
            p = pstore.upsert_field(base, st["slug"], "old_price", new_old)
        except KeyError:
            pending.pop(cid, None)
            reply(base, cid, "Mahsulot topilmadi.")
            return True
        pending.pop(cid, None)
        reply(base, cid, f"✅ Eski narx yangilandi!\n\n{product_detail_text(p)}")
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
        if text.lower().startswith("http"):
            try:
                p = pstore.upsert_field(base, st.get("slug"), "photo", text[:500])
            except KeyError:
                pending.pop(cid, None)
                reply(base, cid, "Mahsulot topilmadi.")
                return True
            pending.pop(cid, None)
            reply(base, cid, f"✅ Rasm yangilandi!\n\n{product_detail_text(p)}")
            return True
        reply(base, cid, "🖼 Rasmni foto ko'rinishida yuboring (yoki rasm havolasi https://...):")
        return True
    if op == "add":
        return handle_add_text(base, cid, text, st)
    pending.pop(cid, None)
    return False


# --- mahsulot qo'shish wizard (SAMA uslubi: tugmalar + custom) ---
ADD_STEPS = ["name", "cat", "price", "old", "stock", "desc", "photo"]
ADD_FIELD_LBL = {"price": "Narx", "old": "Eski narx", "stock": "Qoldiq", "desc": "Tavsif"}
ADD_CANCEL = "\n\n<i>/cancel — bekor qilish</i>"
PRICE_PRESETS = [250000, 350000, 500000, 750000, 1000000, 1500000]
STOCK_PRESETS = [5, 10, 20, 50]


def add_step_kb(step: str) -> dict:
    cancel = [[{"text": "❌ Bekor qilish", "callback_data": "padd:cancel"}]]
    if step == "cat":
        rows = [[{"text": c["name"], "callback_data": f"padd:cat:{c['slug']}"} for c in CATEGORIES[i:i + 2]]
                for i in range(0, len(CATEGORIES), 2)]
        return {"inline_keyboard": rows + cancel}
    if step == "price":
        rows = [[{"text": _fm(v), "callback_data": f"padd:set:price:{v}"} for v in PRICE_PRESETS[i:i + 3]]
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
        "name": f"{n}/7 — Mahsulot nomini yozing (masalan: Qizil atirgul — 25 dona):",
        "cat": f"{n}/7 — Kategoriyani tanlang:",
        "price": f"{n}/7 — Narxni tanlang (so'm):",
        "old": f"{n}/7 — Eski narx (chegirma uchun):",
        "stock": f"{n}/7 — Qoldiq sonini tanlang (dona):",
        "desc": f"{n}/7 — Qisqa tavsif yozing:",
        "photo": f"{n}/7 — Gul rasmini foto qilib yuboring:",
    }.get(step, "Davom eting:")


def add_send_step(base: Path, cid: int) -> None:
    st = pending.get(cid)
    if not st or st.get("op") != "add":
        return
    if st.get("step", 0) >= len(ADD_STEPS):
        add_send_confirm(base, cid)
        return
    step = ADD_STEPS[st["step"]]
    try:
        tg.call_api(base, "sendMessage", {"chat_id": cid,
            "text": add_prompt(step) + ADD_CANCEL, "parse_mode": "HTML",
            "reply_markup": json.dumps(add_step_kb(step))}, timeout=15)
    except Exception as e:
        log.warning("add step xatosi: %s", e)


def add_start(base: Path, cid: int) -> None:
    pending[cid] = {"op": "add", "step": 0, "data": {}}
    add_send_step(base, cid)


def add_cancel(base: Path, cid: int) -> None:
    if pending.pop(cid, None):
        reply(base, cid, "❌ Mahsulot qo'shish bekor qilindi.")
    else:
        reply(base, cid, "ℹ️ Faol wizard yo'q.")


def add_advance(base: Path, cid: int) -> None:
    st = pending.get(cid)
    if not st:
        return
    st.pop("await_custom", None)
    st["step"] = st.get("step", 0) + 1
    add_send_step(base, cid)


def add_store(base: Path, cid: int, field: str, value: str):
    st = pending.get(cid)
    d = st["data"]
    if field == "name":
        if not value or len(value) < 3:
            return "⛔ Nom bo'sh bo'lmasin."
        d["name"] = value[:80]
    elif field == "price":
        v = _parse_money(value)
        if v is None:
            return "⛔ Narx faqat raqam bo'lsin."
        d["price"] = v
    elif field == "old":
        if value == "-":
            d["old_price"] = None
        else:
            v = _parse_money(value)
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
        if value == "-":
            d["description"] = ""
        elif len(value) < 3:
            return "⛔ Tavsif juda qisqa."
        else:
            d["description"] = value[:500]
    elif field == "photo":
        if value == "-":
            d.pop("photo", None)
        else:
            d["photo"] = value[:500]
    else:
        return "⛔ Noma'lum maydon."
    if d.get("category") and "img" not in d:
        d["img"] = dict(pstore.IMG_DEFAULTS.get(d["category"], pstore.IMG_DEFAULTS["buketlar"]))
    d.setdefault("is_featured", 0)
    return None


def add_pick_cat(base: Path, cid: int, slug: str, answer) -> None:
    st = pending.get(cid)
    if not st or st.get("op") != "add" or ADD_STEPS[st.get("step", 99)] != "cat":
        answer("Eski tugma ⛔")
        return
    if slug not in [c["slug"] for c in CATEGORIES]:
        answer("Noto'g'ri kategoriya")
        return
    st["data"]["category"] = slug
    answer("Tanlandi ✅")
    add_advance(base, cid)


def add_send_confirm(base: Path, cid: int) -> None:
    st = pending.get(cid)
    d = (st or {}).get("data", {})
    kb = {"inline_keyboard": [[{"text": "✅ Saqlash", "callback_data": "padd:save"},
                               {"text": "❌ Bekor", "callback_data": "padd:cancel"}]]}
    try:
        tg.call_api(base, "sendMessage", {"chat_id": cid,
            "text": ("🧾 <b>Yangi mahsulot</b>\n━━━━━━━━━━━━\n"
                     f"<b>Nom:</b> {_h.escape(d.get('name', ''))}\n"
                     f"<b>Kategoriya:</b> {cat_name(d.get('category', ''))}\n"
                     f"<b>Narx:</b> <code>{_fm(d.get('price', 0))}</code>\n"
                     f"<b>Eski narx:</b> {_fm(d['old_price']) if d.get('old_price') else '—'}\n"
                     f"<b>Qoldiq:</b> {d.get('stock', 0)} dona\n"
                     f"<b>Tavsif:</b> <i>{_h.escape(d.get('description') or '—')}</i>\n"
                     + ("🖼 Rasm biriktirilgan\n" if d.get("photo") else "")
                     + "━━━━━━━━━━━━\nSaqlaymizmi?"),
            "parse_mode": "HTML", "reply_markup": json.dumps(kb)}, timeout=15)
    except Exception as e:
        log.warning("confirm xatosi: %s", e)


def add_save(base: Path, cid: int) -> None:
    st = pending.pop(cid, None)
    if not st or st.get("op") != "add":
        return
    p = pstore.add_product(base, st["data"])
    reply(base, cid, f"✅ <b>{_h.escape(p['name'])}</b> qo'shildi!\nEndi u saytda ko'rinadi.\n\n➕ Yana qo'shish: /addproduct\n📦 Ro'yxat: /products")


def handle_add_text(base: Path, cid: int, text: str, st: dict) -> bool:
    if text.lower() in ("/cancel", "/bekor", "bekor"):
        add_cancel(base, cid)
        return True
    if text.startswith("/"):
        pending.pop(cid, None)
        reply(base, cid, "ℹ️ Mahsulot qo'shish to'xtatildi.")
        return False
    idx = st.get("step", 0)
    if idx >= len(ADD_STEPS):
        return False
    step = ADD_STEPS[idx]
    if step == "cat":
        reply(base, cid, "👆 Kategoriyani yuqoridagi tugmalardan tanlang.")
        add_send_step(base, cid)
        return True
    if step == "photo":
        if text.lower().startswith("http"):
            err = add_store(base, cid, "photo", text)
            if err:
                reply(base, cid, err)
                return True
            add_advance(base, cid)
            return True
        if text.lower() in ("skip", "o'tkazish", "o'tkazib yuborish", "0", "-", "yo'q"):
            add_store(base, cid, "photo", "-")
            add_advance(base, cid)
            return True
        reply(base, cid, "📸 Rasmni foto qilib yuboring, URL yozing, «o'tkazish» yoki «-» deb yozing.")
        return True
    if step in ("price", "old", "stock", "desc", "name"):
        st.pop("await_custom", None)
        err = add_store(base, cid, step, text)
        if err:
            reply(base, cid, err + "\n\nTugmalardan tanlang yoki to'g'ri yozing.")
            return True
        add_advance(base, cid)
        return True
    pending.pop(cid, None)
    return False


def handle_padd_callback(base: Path, cb: dict) -> None:
    data = cb.get("data", "")
    msg = cb.get("message") or {}
    cid = (msg.get("chat") or {}).get("id")
    qid = cb.get("id")

    def answer(t: str) -> None:
        try:
            tg.call_api(base, "answerCallbackQuery", {"callback_query_id": qid, "text": t}, timeout=10)
        except Exception:
            pass

    rest = data.split(":", 2)
    what = rest[1] if len(rest) > 1 else ""
    arg = rest[2] if len(rest) > 2 else ""
    if what == "new":
        answer("")
        add_start(base, cid)
        return
    if what == "cancel":
        answer("Bekor qilindi")
        add_cancel(base, cid)
        return
    if what == "save":
        answer("Saqlanmoqda...")
        add_save(base, cid)
        return
    st = pending.get(cid)
    if not st or st.get("op") != "add":
        answer("Eski tugma ⛔")
        return
    step = ADD_STEPS[st.get("step", 99)] if st.get("step", 99) < len(ADD_STEPS) else None
    if what == "cat":
        add_pick_cat(base, cid, arg, answer)
        return
    if what == "set":
        field, _, value = arg.partition(":")
        if step != field:
            answer("Eski tugma ⛔")
            return
        err = add_store(base, cid, field, value)
        if err:
            answer(err)
            return
        answer("Saqlangan ✅")
        add_advance(base, cid)
        return
    if what == "custom":
        if step != arg:
            answer("Eski tugma ⛔")
            return
        st["await_custom"] = arg
        lbl = ADD_FIELD_LBL.get(arg, arg)
        answer("")
        reply(base, cid, f"✍️ <b>{lbl}</b> ni yozib yuboring:{ADD_CANCEL}")
        return
    answer("Noma'lum buyruq")


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
    if op == "add" and st.get("step") == ADD_STEPS.index("photo"):
        try:
            d = st["data"]
            path = tg.download_photo(base, file_id, pstore.slugify(d["name"]))
            d["photo"] = path
        except Exception as e:
            log.warning("rasm xatosi: %s", e)
            reply(base, cid, "❌ Rasmni saqlab bo'lmadi. Boshqa rasm yuboring yoki 'o'tkazish' deb yozing:")
            return True
        add_advance(base, cid)
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
            [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    if st in ("yangi",):
        return {"inline_keyboard": [
            [{"text": "✅ Qabul qilish", "callback_data": f"order:{oid}:accepted"},
             {"text": "❌ Rad etish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    if st == "awaiting_payment":
        return {"inline_keyboard": [
            [{"text": "❌ Bekor qilish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    return {"inline_keyboard": [
        [{"text": "🟡 Tayyorlanmoqda", "callback_data": f"order:{oid}:preparing"},
         {"text": "🚚 Yo'lda", "callback_data": f"order:{oid}:delivering"}],
        [{"text": "🏁 Yetkazildi", "callback_data": f"order:{oid}:delivered"},
         {"text": "❌ Bekor", "callback_data": f"order:{oid}:cancelled"}],
        [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}


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
    prev = o.get("status", "yangi")
    o["status"] = status
    if by:
        o["accepted_by"] = by
    _save_orders(base, orders)
    refresh_order_msgs(base, o)
    notify_user_status(base, o, status, prev)
    return o


def notify_user_status(base: Path, o: dict, status: str, prev: str = "") -> None:
    if not o.get("tg_user"):
        return
    ust = user_status_text(o)
    text, kb = "", None
    if status == "accepted" and prev == "awaiting_confirm":
        text = f"✅ <b>To'lov tasdiqlandi!</b>\n{ust}\n⏳ Tayyorlanmoqda, kuting."
    elif status == "rejected":
        text = f"❌ <b>Buyurtma rad etildi.</b>\n{ust}\nChek tasdiqlanmadi yoki xato topildi. Operatorimiz bog'lanadi."
    elif status == "preparing":
        text = f"🟡 <b>Buyurtmangiz tayyorlanmoqda...</b>\n{ust}"
    elif status == "delivering":
        text = f"🚚 <b>Buyurtmangiz yo'lda!</b>\n{ust}"
    elif status == "delivered":
        text = f"📦 <b>Buyurtma yetkazildi!</b>\n{ust}\nQabul qildingizmi?"
        kb = {"inline_keyboard": [[{"text": "✅ Qabul qildim", "callback_data": f"recv:{o['id']}"}]]}
    elif status == "cancelled":
        text = f"❌ <b>Buyurtma bekor qilindi.</b>\n{ust}"
    if not text:
        return
    try:
        tg.call_api(base, "sendMessage", {"chat_id": o["tg_user"], "text": text, "parse_mode": "HTML",
            **({"reply_markup": json.dumps(kb)} if kb else {})}, timeout=15)
    except Exception as e:
        log.warning("user notify xatosi: %s", e)


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


def filt_counts(base: Path) -> dict:
    orders = _orders(base)
    out = {}
    for f, (_, statuses) in FILTERS.items():
        out[f] = len(orders) if statuses is None else sum(1 for o in orders if o.get("status", "yangi") in statuses)
    return out


def send_orders_list(base: Path, cid: int, filt: str = "pending", page: int = 0, edit_mid: int = 0) -> None:
    if filt not in FILTERS:
        filt = "pending"
    orders = filtered_orders(base, filt)
    maxpage = max(0, (len(orders) - 1) // PAGE_SIZE)
    page = max(0, min(page, maxpage))
    chunk = orders[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    label = FILTERS[filt][0]
    counts = filt_counts(base)
    head = f"📋 <b>Buyurtmalar · {label}</b>\n<i>Jami: {len(orders)} ta · Sahifa {page + 1}/{maxpage + 1}</i>"
    if not chunk:
        text = head + "\n\n📭 Bu bo'limda buyurtma yo'q."
    else:
        lines = [f"{st_label(o.get('status', ''))} <b>{o.get('no', '')}</b>\n   👤 {_h.escape(o.get('name', ''))} · 💰 <b>{_fm(o.get('total', 0))} so'm</b> · <code>#{o['id']}</code>"
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
    kb_rows = [[{"text": f"#{o['id']} {o.get('no', '')}", "callback_data": f"view:{o['id']}"}] for o in chunk]
    nav = []
    if page > 0:
        nav.append({"text": "⬅️ Oldingi", "callback_data": f"olist:{filt}:{page - 1}"})
    nav.append({"text": f"· {page + 1}/{maxpage + 1} ·", "callback_data": "olist:noop"})
    if page < maxpage:
        nav.append({"text": "Keyingi ➡️", "callback_data": f"olist:{filt}:{page + 1}"})
    kb = {"inline_keyboard": tabs + kb_rows + [nav]}
    if edit_mid:
        edit_to(base, cid, edit_mid, text, kb)
    else:
        try:
            tg.call_api(base, "sendMessage", {"chat_id": cid, "text": text,
                "parse_mode": "HTML", "reply_markup": json.dumps(kb)}, timeout=15)
        except Exception as e:
            log.warning("olist xatosi: %s", e)


def stats_text(base: Path) -> str:
    orders = _orders(base)
    t = date.today().isoformat()
    today = [o for o in orders if str(o.get("created_at", "")).startswith(t)]
    total = sum(o.get("total", 0) for o in orders)
    today_sum = sum(o.get("total", 0) for o in today)
    by_st: dict[str, int] = {}
    for o in orders:
        by_st[o.get("status", "yangi")] = by_st.get(o.get("status", "yangi"), 0) + 1
    out = ["📊 <b>Statistika</b>", "",
           "📦 <b>Jami</b>",
           f"{len(orders)} ta · <b>{_fm(total)} so'm</b>", "",
           "📅 <b>Bugun</b>",
           f"{len(today)} ta · <b>{_fm(today_sum)} so'm</b>",
           "━━━━━━━━━━━━",
           "<b>Holatlar bo'yicha</b>", ""]
    if by_st:
        for s, n in by_st.items():
            out.append(f"{st_label(s)} — <b>{n} ta</b>")
    else:
        out.append("—")
    return "\n".join(out)


def promo_list_text(base: Path) -> str:
    from app import payments as paymod
    promos = paymod.list_promos(base)
    if not promos:
        return "🎟 Promokodlar yo'q.\nYaratish: <code>/promo_add KOD FOIZ [SONI]</code>"
    rows = []
    for code, p in promos.items():
        if p.get("max_uses"):
            left = f"{p.get('used', 0)}/{p.get('max_uses')}"
        else:
            left = "cheksiz"
        rows.append(f"🎟 <code>{_h.escape(code)}</code> — <b>{p.get('pct')}%</b> <i>({left})</i>")
    return "🎟 <b>Promokodlar</b>\n\n" + "\n".join(rows)


def send_promos(base: Path, cid: int) -> None:
    from app import payments as paymod
    promos = paymod.list_promos(base)
    kb = None
    if promos:
        kb = {"inline_keyboard": [[{"text": f"❌ {code}", "callback_data": f"promo_del:{code}"}] for code in promos]
              + [[{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    try:
        tg.call_api(base, "sendMessage", {"chat_id": cid, "text": promo_list_text(base),
            "parse_mode": "HTML", **({"reply_markup": json.dumps(kb)} if kb else {})}, timeout=15)
    except Exception as e:
        log.warning("promos xatosi: %s", e)


def promo_add_cmd(base: Path, text: str) -> str:
    parts = text.split()
    if len(parts) < 3:
        return "♻️ Format: <code>/promo_add KOD FOIZ [SONI]</code>\nMasalan: <code>/promo_add SALOM10 10 50</code> — 10% li, 50 marta."
    try:
        pct = int(parts[2])
    except (ValueError, IndexError):
        return "⛔ Foiz butun son bo'lsin (1-90)."
    try:
        from app import payments as paymod
        mx = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
        p = paymod.add_promo(base, parts[1], pct, mx)
        return f"✅ Promokod yaratildi: <b>{_h.escape(p['code'])}</b> — {p['pct']}%" + (f" ({mx} marta)" if mx else " (cheksiz)")
    except (ValueError, IndexError) as e:
        return f"⛔ {e}"


def card_text(base: Path) -> str:
    from app import payments as paymod
    card = (paymod.get_payment(base).get("pay_card") or "").strip()
    if card:
        return f"💳 Karta: <code>{_h.escape(card)}</code>"
    return "💳 Karta kiritilmagan. /setcard"


def payment_instructions(base: Path, o: dict) -> str:
    from app import payments as paymod
    pay = paymod.get_payment(base)
    card = pay.get("pay_card", "")
    digits = "".join(ch for ch in str(card or "") if ch.isdigit())
    pretty = " ".join(digits[i:i + 4] for i in range(0, len(digits), 4))
    pct = pay.get("prepay_pct", 50)
    prepay = o.get("prepay")
    if prepay is None:
        prepay = round(o.get("total", 0) * pct / 100)
    sep = "━━━━━━━━━━━━━━━━━━━━"
    if card:
        card_block = f"💳 <b><u>KARTA RAQAMI</u></b>  <i>(bosing — nusxa olinadi)</i>\n<pre>{_h.escape(pretty or card)}</pre>"
    else:
        card_block = "💳 Karta raqamini operatorimiz shu chatga yuboradi."
    return (
        f"🧾 <b>Buyurtma {o.get('no', '')}</b>\n"
        f"{sep}\n"
        f"💰 Jami summa: {_fm(o.get('total', 0))} so'm\n"
        f"💵 Oldindan to'lov — {pct}%:\n"
        f"<pre>{_fm(prepay)}</pre>\n"
        f"{sep}\n"
        f"⛔️ <b><u>MUHIM: Aynan yuqoridagi summani to'lang!</u></b>\n"
        f"❌ <b>Ko'p ham, kam ham yubormang</b> — tiyinma-tiyin to'g'ri kelishi shart.\n"
        f"<i>Noto'g'ri summa tushsa, chek tasdiqlanmaydi va buyurtmangiz kechikadi.</i>\n"
        f"{sep}\n"
        f"{card_block}\n"
        f"{sep}\n"
        "📸 <b>1-qadam:</b> To'lovni qiling.\n"
        "📸 <b>2-qadam:</b> Chekni shu chatga <b>rasm</b> qilib yuboring.\n"
        "✅ Chek tasdiqlangach, buyurtma adminga o'tadi."
    )


def user_status_text(o: dict) -> str:
    return (f"📦 <b>Buyurtma {_h.escape(o.get('no', ''))}</b>\n{st_label(o.get('status', ''))}\n\n"
            f"💰 Jami: <b>{_fm(o.get('total', 0))} so'm</b>")


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
        reply(base, cid, f"{user_status_text(o)}\n\n/myorders — buyurtmalarim")


def handle_check(base: Path, cid: int, msg: dict) -> bool:
    """Mijoz chek rasmini yuborsa — adminlarga forward + awaiting_confirm."""
    if pending.get(cid):
        return False
    try:
        if is_admin(base, cid, (msg.get("from") or {}).get("username", "")):
            if msg.get("photo"):
                reply(base, cid, "ℹ️ Chekni mijoz yuboradi.")
                return True
            return False
    except Exception:
        pass
    photos = msg.get("photo") or []
    if not photos:
        return False
    orders = _orders(base)
    o = next((x for x in orders[::-1]
              if x.get("tg_user") == cid and x.get("status") in ("awaiting_payment", "yangi")), None)
    if not o:
        reply(base, cid, "📭 To'lov kutilayotgan buyurtmangiz topilmadi.\nSaytdan buyurtma bering: azaflowers.uz")
        return True
    if o.get("prepay") is None:
        o["prepay"] = round(o.get("total", 0) / 2)
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
            if o.get("lat") and o.get("lon"):
                tg.call_api(base, "sendLocation", {
                    "chat_id": admin, "latitude": o["lat"],
                    "longitude": o["lon"]}, timeout=15)
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
    reply(base, cid, f"✅ <b>Chek qabul qilindi!</b>\n{user_status_text(o)}\n🔎 Admin tekshirmoqda, kuting...")
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
    elif data == "orders:10" or data.startswith("orders:"):
        parts = data.split(":")
        filt = parts[1] if len(parts) > 2 and parts[1] in FILTERS else "pending"
        try:
            page = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            page = 0
        send_orders_list(base, cid, filt, page)
        answer("")
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
        kb = order_keyboard(o)
        try:
            tg.call_api(base, "sendMessage", {"chat_id": cid,
                "text": f"{_ot(o)}", "parse_mode": "HTML",
                **({"reply_markup": json.dumps(kb)} if kb else {})}, timeout=15)
        except Exception as e:
            log.warning("view xatosi: %s", e)
        answer("")
    elif data == "stats":
        reply(base, cid, stats_text(base))
        answer("Statistika")
    elif data == "promos":
        send_promos(base, cid)
        answer("")
    elif data == "ocard":
        reply(base, cid, card_text(base))
        answer("Karta")
    elif data.startswith("promo_del:"):
        from app import payments as paymod
        ok = paymod.del_promo(base, data.split(":", 1)[1])
        answer("O'chirildi 🗑" if ok else "Topilmadi")
        if ok:
            send_promos(base, cid)
    elif data.startswith("panel:"):
        what = data.split(":", 1)[1]
        if what == "orders":
            send_orders_list(base, cid, "pending", 0, edit_mid=mid or 0)
        elif what == "stats":
            reply(base, cid, stats_text(base))
        elif what == "products":
            send_product_list(base, cid)
        elif what == "promos":
            reply(base, cid, promo_list_text(base))
        elif what == "card":
            reply(base, cid, card_text(base))
        answer("Panel")
    else:
        answer("Noma'lum buyruq")


def send_panel(base: Path, cid: int) -> None:
    kb = {"inline_keyboard": [
        [{"text": "📋 Buyurtmalar", "callback_data": "orders:10"}],
        [{"text": "➕ Mahsulot qo'shish", "callback_data": "padd:new"},
         {"text": "📦 Mahsulotlar", "callback_data": "products"}],
        [{"text": "📊 Statistika", "callback_data": "stats"},
         {"text": "🎟 Promokodlar", "callback_data": "promos"}]]}
    try:
        tg.call_api(base, "sendMessage", {"chat_id": cid,
            "text": "👋 <b>AZA FLOWERS — admin panel</b>\n━━━━━━━━━━━━\n📋 /orders — <i>buyurtmalar</i>\n➕ /addproduct — <i>mahsulot qo'shish</i>\n📦 /products — <i>mahsulotlar</i>\n📊 /stats — <i>statistika</i>\n🎟 /promo_list — <i>promokodlar</i>",
            "parse_mode": "HTML", "reply_markup": json.dumps(kb)}, timeout=15)
    except Exception as e:
        log.warning("panel xatosi: %s", e)


def send_myorders(base: Path, cid: int) -> None:
    orders = [o for o in _orders(base)[::-1] if o.get("tg_user") == cid][:5]
    if not orders:
        reply(base, cid, "📭 Buyurtmalaringiz topilmadi.")
        return
    lines = [f"{st_label(o.get('status', ''))} <b>{o.get('no', '')}</b>\n   💰 <b>{_fm(o.get('total', 0))} so'm</b>"
             for o in orders]
    kb_rows = [[{"text": f"✅ Qabul qildim ({o.get('no', '')})", "callback_data": f"recv:{o['id']}"}]
               for o in orders if o.get("status") == "delivered"]
    kb = {"inline_keyboard": kb_rows} if kb_rows else None
    try:
        tg.call_api(base, "sendMessage", {"chat_id": cid,
            "text": "📦 <b>Buyurtmalarim</b>\n\n" + "\n\n".join(lines),
            "parse_mode": "HTML", **({"reply_markup": json.dumps(kb)} if kb else {})}, timeout=15)
    except Exception as e:
        log.warning("myorders xatosi: %s", e)
