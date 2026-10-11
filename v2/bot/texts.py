"""SAMA uslubidagi matnlar va klaviaturalar (sof funksiyalar — testlanadi)."""
import html as _h

DIV = "━━━━━━━━━━━━"
SEP = "━━━━━━━━━━━━━━━━━━━━"
PAGE_SIZE = 5

STATUS_UZ = {
    "new": "🆕 Yangi",
    "awaiting_payment": "⏳ To'lov kutilmoqda",
    "awaiting_verify": "🔎 Chek tekshirilmoqda",
    "confirmed": "✅ Tasdiqlangan",
    "preparing": "🟡 Tayyorlanmoqda",
    "ready": "📦 Tayyor",
    "delivering": "🚚 Yo'lda",
    "delivered": "🏁 Yetkazildi",
    "closed": "🎉 Yakunlandi",
    "cancelled": "❌ Bekor qilindi",
}

FILTERS = {
    "pending": ("Kutulmoqda", ["new", "awaiting_payment", "awaiting_verify"]),
    "accepted": ("Qabul qilingan", ["confirmed", "preparing", "ready", "delivering", "delivered", "closed"]),
    "rejected": ("Rad etilgan", ["cancelled"]),
    "all": ("Barchasi", None),
}

PAY_UZ = {
    "awaiting_advance_payment": "Oldindan to'lov kutilmoqda",
    "awaiting_card_payment_verification": "Karta to'lovi tekshiruvi",
    "receipt_submitted": "Chek yuborilgan",
    "advance_payment_confirmed": "Oldindan to'lov tasdiqlangan",
    "partially_paid": "Qisman to'langan",
    "receipt_rejected": "Chek rad etilgan",
    "fully_paid": "To'liq to'langan",
    "refund_pending": "Qaytarish kutilmoqda",
    "refunded": "Qaytarilgan",
}


def fm(n) -> str:
    try:
        return f"{int(float(n)):,}".replace(",", " ")
    except Exception:
        return str(n)


def st_label(s: str) -> str:
    return STATUS_UZ.get(s, s)


def order_keyboard(o: dict):
    st = o.get("status", "new")
    oid = o["id"]
    if st in ("delivered", "closed", "cancelled"):
        return None
    if st == "awaiting_verify":
        return {"inline_keyboard": [
            [{"text": "✅ Chekni tasdiqlash", "callback_data": f"order:{oid}:confirmed"},
             {"text": "❌ Rad etish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    if st == "awaiting_payment":
        return {"inline_keyboard": [
            [{"text": "❌ Bekor qilish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    if st == "new":
        return {"inline_keyboard": [
            [{"text": "✅ Qabul qilish", "callback_data": f"order:{oid}:confirmed"},
             {"text": "❌ Rad etish", "callback_data": f"order:{oid}:cancelled"}],
            [{"text": "📋 Ro'yxat", "callback_data": "orders:10"}]]}
    flow = {"confirmed": ("preparing", "🟡 Tayyorlanmoqda"),
            "preparing": ("ready", "📦 Tayyor"),
            "ready": ("delivering", "🚚 Yo'lda"),
            "delivering": ("delivered", "🏁 Yetkazildi")}
    rows = []
    if st in flow:
        nxt, lbl = flow[st]
        rows.append([{"text": f"{lbl} →", "callback_data": f"order:{oid}:{nxt}"}])
    rows.append([{"text": "❌ Bekor", "callback_data": f"order:{oid}:cancelled"}])
    rows.append([{"text": "📋 Ro'yxat", "callback_data": "orders:10"}])
    return {"inline_keyboard": rows}


def order_text(o: dict) -> str:
    lines = "\n".join(f"{i}. {_h.escape(x.get('name', ''))} × {x.get('qty', 0)} = {fm(x.get('line_total', 0))}"
                      for i, x in enumerate(o.get("items", []) or [], 1)) or "—"
    p = o.get("payment") or {}
    parts = [
        f"🛍 <b>Buyurtma {o.get('no', '')}</b> · <code>#{o.get('id', '')}</code>",
        st_label(o.get("status", "")),
        DIV,
        "<b>👤 Mijoz</b>",
        "",
        f"<b>Ism:</b> {_h.escape(o.get('name', ''))}",
        f"<b>Tel:</b> <code>{_h.escape(o.get('phone', ''))}</code>",
        f"<b>Manzil:</b> {_h.escape(', '.join(x for x in [o.get('region', ''), o.get('city', ''), o.get('address', '')] if x))}",
        f"<b>Yetkazish:</b> {_h.escape(o.get('ship_method', ''))}",
        f"<b>To'lov:</b> {_h.escape(o.get('pay_method', ''))}",
        f"<b>Izoh:</b> <i>{_h.escape(o.get('note') or '—')}</i>",
        DIV,
        "<b>🧾 Tarkib</b>",
        "",
        f"<pre>{_h.escape(lines)}</pre>",
        DIV,
        "<b>💰 Hisob</b>",
        "",
        f"Mahsulotlar: {fm(o.get('subtotal', 0))} so'm",
    ]
    if float(o.get("discount", 0) or 0):
        parts.append(f"🎟 <b>Chegirma:</b> −{fm(o['discount'])} so'm")
    parts.append(f"💰 <b>Jami: {fm(o.get('total', 0))} so'm</b>")
    if p:
        parts.append(f"💳 <b>Oldindan:</b> <b>{fm(p.get('required_amount', 0))}</b>")
        parts.append(f"💵 <b>Qabul:</b> {fm(p.get('received', 0))} · <b>Qolgan:</b> {fm(p.get('remaining', 0))}")
        parts.append(f"To'lov holati: {PAY_UZ.get(p.get('status', ''), p.get('status', ''))}")
    return "\n".join(parts)


def user_status_text(o: dict) -> str:
    return (f"📦 <b>Buyurtma {_h.escape(o.get('no', ''))}</b>\n{st_label(o.get('status', ''))}\n\n"
            f"💰 Jami: <b>{fm(o.get('total', 0))} so'm</b>")


def payment_instructions(o: dict, card: dict) -> str:
    p = o.get("payment") or {}
    req = p.get("required_amount", o.get("total", 0))
    pretty = "".join(ch for ch in str(card.get("card_number", "")) if ch.isdigit())
    pretty = " ".join(pretty[i:i + 4] for i in range(0, len(pretty), 4))
    if card.get("card_number"):
        card_block = (f"💳 <b><u>KARTA RAQAMI</u></b>  <i>(bosing — nusxa olinadi)</i>\n<pre>{_h.escape(pretty)}</pre>"
                      + (f"\n👤 {_h.escape(card.get('cardholder', ''))}" if card.get("cardholder") else ""))
    else:
        card_block = "💳 Karta raqamini operatorimiz shu chatga yuboradi."
    return (
        f"🧾 <b>Buyurtma {o.get('no', '')}</b>\n"
        f"{SEP}\n"
        f"💰 Jami summa: {fm(o.get('total', 0))} so'm\n"
        f"💵 Oldindan to'lov:\n"
        f"<pre>{fm(req)}</pre>\n"
        f"{SEP}\n"
        f"⛔️ <b><u>MUHIM: Aynan yuqoridagi summani to'lang!</u></b>\n"
        f"{SEP}\n"
        f"{card_block}\n"
        f"{SEP}\n"
        "📸 <b>1-qadam:</b> To'lovni qiling.\n"
        "📸 <b>2-qadam:</b> Chekni shu chatga <b>rasm</b> qilib yuboring."
    )


PANEL_TEXT = ("👋 <b>FAX Flores — admin panel</b>\n━━━━━━━━━━━━\n<b>Buyruqlar</b>\n\n"
              "📋 /orders — <i>buyurtmalar</i>\n📊 /stats — <i>statistika</i>\n"
              "➕ /addproduct — <i>yangi mahsulot</i>\n📦 /products — <i>mahsulotlar</i>\n"
              "🎟 /promo_add KOD FOIZ [SONI] — <i>promokod</i>\n💳 /setcard KARTA — <i>karta</i>\nℹ️ /help — <i>yordam</i>")

PANEL_KB = {"inline_keyboard": [
    [{"text": "📋 Buyurtmalar", "callback_data": "orders:10"}],
    [{"text": "➕ Mahsulot qo'shish", "callback_data": "padd:new"},
     {"text": "📦 Mahsulotlar", "callback_data": "products"}],
    [{"text": "📊 Statistika", "callback_data": "stats"},
     {"text": "🎟 Promokodlar", "callback_data": "promos"}]]}

USER_WELCOME = ("👋 <b>FAX Flores</b> do'kon boti.\n\n"
                "Buyurtma berish uchun saytdan buyurtma qoldiring — to'lov uchun shu botga link beriladi.\n\n"
                "/myorders — buyurtmalarim")

HELP_TEXT = ("ℹ️ Yangi buyurtma kelganda tugmalar bilan xabar keladi:\n"
             "✅ Qabul — tayyorlashga o'tkazish\n"
             "📦 → 🚚 → 🏁 — holatni yangilang\n"
             "❌ — bekor qilingan\n\n"
             "➕ Mahsulot qo'shish: /addproduct\n"
             "📦 Mahsulotlar: /products · o'chirish: /delproduct SLUG\n"
             "🎟 Promokod: /promo_add KOD FOIZ [SONI]\n"
             "💳 Karta: /setcard KARTA")
