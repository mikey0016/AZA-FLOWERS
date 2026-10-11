from __future__ import annotations
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.seed import CATEGORIES, DELIVERY_NOTE, CONTACT
from app import store as pstore
from app import users as usersmod
from app import payments as paymod
from app.bot import load_chats
from app.telegram import broadcast_order, get_updates, load_settings as tg_settings, notify_admins, order_text

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
ORDERS_FILE = BASE_DIR / "orders.json"
STATIC_DIR.mkdir(exist_ok=True)

def page(name: str) -> FileResponse:
    """HTML sahifalar keshlanmasin — har doim yangi versiya."""
    return FileResponse(STATIC_DIR / name, headers={"Cache-Control": "no-store, max-age=0"})

# SAMA uslubidagi to'lov: viloyatlar + yetkazish turlari
REGIONS = ["Toshkent shahri", "Toshkent viloyati", "Samarqand", "Buxoro", "Andijon",
           "Farg'ona", "Namangan", "Qashqadaryo", "Surxondaryo", "Xorazm",
           "Navoiy", "Jizzax", "Sirdaryo", "Qoraqalpog'iston"]
SHIP_OPTIONS = [
    {"slug": "standard", "name": "Standart", "hint": "Yandex orqali 3 soatgacha · alohida to'lanadi", "fee": 0},
    {"slug": "express", "name": "Tezkor", "hint": "1 soatda · +30 000 so'm", "fee": 30000},
]
SHIP_FEE = {s["slug"]: s["fee"] for s in SHIP_OPTIONS}
SHIP_LABEL = {"standard": "Standart (Yandex, 3 soat)", "express": "Tezkor (1 soat)"}
PAY_LABEL = {"cash": "Naqd / yetkazib berishda", "card": "Plastik karta (terminal)",
             "online": "Online to'lov (Click / Payme)"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    if tg_settings(BASE_DIR)["bot_token"]:
        import threading
        from app import bot as botmod
        threading.Thread(target=botmod.run_polling, args=(BASE_DIR,), daemon=True).start()
    yield

app = FastAPI(title="AZA FLOWERS", version="1.0.0", lifespan=lifespan)

# --- helpers ---
def product_card(p: dict) -> dict:
    d = 0
    if p.get("old_price"):
        d = round((p["old_price"] - p["price"]) / p["old_price"] * 100)
    return {**p, "discount_pct": d}

def calc_totals(items: list[dict]) -> dict:
    by_slug = {p["slug"]: p for p in pstore.get_products(BASE_DIR)}
    lines = []
    subtotal = 0
    for it in items:
        p = by_slug.get(it.get("slug", ""))
        if not p:
            raise HTTPException(400, f"Noma'lum mahsulot: {it.get('slug')}")
        qty = max(1, min(50, int(it.get("qty", 1))))
        if qty > p["stock"]:
            raise HTTPException(400, f"«{p['name']}» dan faqat {p['stock']} dona qoldi")
        line_total = p["price"] * qty
        subtotal += line_total
        lines.append({"slug": p["slug"], "name": p["name"], "price": p["price"], "qty": qty, "total": line_total})
    delivery = 0  # Yandex haqi mijoz tomonidan alohida to'lanadi
    return {"lines": lines, "subtotal": subtotal, "delivery": delivery, "total": subtotal + delivery, "delivery_note": DELIVERY_NOTE}

def load_orders() -> list:
    if ORDERS_FILE.exists():
        try:
            return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_order(order: dict):
    orders = load_orders()
    orders.append(order)
    ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")

# --- API ---
@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/api/restart")
async def api_restart(key: str = ""):
    """pm2 orqali qayta ishga tushirish (restart.key fayli bo'lganda)."""
    try:
        want = (BASE_DIR / "restart.key").read_text().strip()
    except Exception:
        raise HTTPException(403, "yo'q")
    if not key or key != want:
        raise HTTPException(403, "yo'q")
    import threading
    threading.Timer(1.0, lambda: os._exit(0)).start()
    return {"ok": True, "msg": "restarting"}

@app.get("/api/config")
async def config():
    pay = paymod.get_payment(BASE_DIR)
    return {"delivery_fee": 0, "free_delivery_from": None, "delivery_note": DELIVERY_NOTE,
            "contact": CONTACT, "pay_card": pay["pay_card"], "prepay_pct": pay["prepay_pct"],
            "regions": REGIONS, "ship": SHIP_OPTIONS}

@app.get("/api/categories")
async def categories():
    counts = {}
    for p in pstore.get_products(BASE_DIR):
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    return [{"total": counts.get(c["slug"], 0), **c} for c in CATEGORIES]

@app.get("/api/products")
async def list_products(q: str = "", category: str = "", sort: str = "popular", featured: str = ""):
    items = [product_card(p) for p in pstore.get_products(BASE_DIR)]
    if category and category != "all":
        items = [p for p in items if p["category"] == category]
    if featured == "1":
        items = [p for p in items if p.get("is_featured")]
    if q:
        ql = q.lower()
        items = [p for p in items if ql in p["name"].lower() or ql in p.get("description", "").lower()]
    if sort == "cheap":
        items.sort(key=lambda p: p["price"])
    elif sort == "expensive":
        items.sort(key=lambda p: -p["price"])
    elif sort == "discount":
        items.sort(key=lambda p: -p["discount_pct"])
    else:  # popular: featured first, then stock
        items.sort(key=lambda p: (-int(p.get("is_featured", 0)), p["price"]))
    return items

@app.get("/api/products/{slug}")
async def product_detail(slug: str):
    all_products = pstore.get_products(BASE_DIR)
    for p in all_products:
        if p["slug"] == slug:
            rel = [product_card(x) for x in all_products if x["category"] == p["category"] and x["slug"] != slug][:4]
            return {**product_card(p), "related": rel}
    raise HTTPException(404, "Mahsulot topilmadi")

class OrderItem(BaseModel):
    slug: str
    qty: int = Field(ge=1, le=50)

class OrderIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=7, max_length=20)
    address: str = Field(min_length=5, max_length=200)
    comment: Optional[str] = ""
    items: list[OrderItem]

@app.post("/api/orders")
async def create_order(o: OrderIn, bg: BackgroundTasks, request: Request):
    totals = calc_totals([x.model_dump() for x in o.items])
    u = usersmod.me_by_token(BASE_DIR, _bearer(request))
    order = {
        "id": int(time.time() * 1000) % 1000000,
        "user_id": u["id"] if u else None,
        "name": o.name.strip(),
        "phone": o.phone.strip(),
        "address": o.address.strip(),
        "comment": (o.comment or "").strip(),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "yangi",
        "accepted_by": None,
        **totals,
    }
    save_order(order)
    bg.add_task(notify_admins, BASE_DIR, order)
    return {"ok": True, "order_id": order["id"], **totals}

@app.get("/api/orders")
async def list_orders():
    return load_orders()[-20:][::-1]

class OrderItem2(BaseModel):
    slug: str
    qty: int = Field(ge=1, le=50)

class OrderNew(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=7, max_length=20)
    region: Optional[str] = ""
    city: Optional[str] = ""
    address: Optional[str] = ""
    note: Optional[str] = ""
    comment: Optional[str] = ""
    ship: Optional[str] = "standard"
    pay: Optional[str] = "cash"
    promo: Optional[str] = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    items: list[OrderItem2]

@app.get("/api/promo")
async def promo_check(code: str = ""):
    return paymod.check_promo(BASE_DIR, code)

@app.post("/api/order")
async def create_order2(o: OrderNew, bg: BackgroundTasks, request: Request):
    totals = calc_totals([x.model_dump() for x in o.items])
    subtotal = totals["subtotal"]
    ship = o.ship if o.ship in SHIP_FEE else "standard"
    ship_cost = SHIP_FEE[ship]
    promo_code = (o.promo or "").strip().upper()
    discount, pct = 0, 0
    if promo_code:
        chk = paymod.check_promo(BASE_DIR, promo_code)
        if not chk.get("ok"):
            raise HTTPException(400, chk.get("error", "Promokod yaroqsiz"))
        pct = chk["pct"]
        discount = round(subtotal * pct / 100)
    total = subtotal - discount + ship_cost
    pay = paymod.get_payment(BASE_DIR)
    prepay = round(total * pay["prepay_pct"] / 100)
    if promo_code:
        paymod.use_promo(BASE_DIR, promo_code)
    u = usersmod.me_by_token(BASE_DIR, _bearer(request))
    oid = int(time.time() * 1000) % 1000000
    addr = ", ".join(x for x in [o.region, o.city, o.address] if x) or o.address
    if o.lat and o.lon and addr and "xaritada" not in addr:
        addr += " (xaritada belgilangan 📍)"
    order = {
        "id": oid, "no": f"AZA-{oid}",
        "user_id": u["id"] if u else None,
        "name": o.name.strip(), "phone": o.phone.strip(),
        "address": addr.strip(), "note": (o.note or "").strip(),
        "comment": (o.comment or "").strip(),
        "lat": o.lat, "lon": o.lon,
        "ship": ship, "ship_label": SHIP_LABEL[ship],
        "pay": o.pay if o.pay in PAY_LABEL else "cash",
        "pay_label": PAY_LABEL.get(o.pay, PAY_LABEL["cash"]),
        "promo": promo_code, "discount": discount, "discount_pct": pct,
        "subtotal": subtotal, "ship_cost": ship_cost,
        "total": total, "prepay": prepay,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "awaiting_payment",
        "accepted_by": None, "tg_user": None, "check_file": "", "notified": 0,
        **{"lines": totals["lines"], "delivery": ship_cost,
           "delivery_note": DELIVERY_NOTE},
    }
    save_order(order)
    from app import telegram as tgmod
    return {"ok": True, "id": oid, "no": order["no"], "order_id": oid,
            "discount": discount, "total": total, "prepay": prepay,
            "bot_url": tgmod.order_bot_url(BASE_DIR, oid)}

@app.get("/api/order")
async def order_status(id: int):
    for o in load_orders():
        if o.get("id") == id:
            return {"ok": True, "id": o["id"], "no": o.get("no", f"AZA-{o['id']}"),
                    "status": o.get("status", "yangi"), "total": o.get("total", 0),
                    "prepay": o.get("prepay", 0)}
    raise HTTPException(404, "Buyurtma topilmadi")

@app.get("/api/telegram/status")
async def tg_status():
    s = tg_settings(BASE_DIR)
    return {"configured": bool(s["bot_token"]), "admins": len(s["admin_chat_ids"])}

@app.get("/api/telegram/updates")
async def tg_updates():
    s = tg_settings(BASE_DIR)
    if not s["bot_token"]:
        raise HTTPException(400, "Bot token sozlanmagan. Avval telegram.json ga token qo'ying.")
    return {"known": load_chats(BASE_DIR), "recent": get_updates(BASE_DIR)}

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=4, max_length=64)

class LoginIn(BaseModel):
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=1, max_length=64)

def _bearer(request: Request) -> str:
    h = request.headers.get("authorization", "")
    return h[7:] if h.lower().startswith("bearer ") else ""

@app.post("/api/auth/register")
async def auth_register(r: RegisterIn):
    try:
        return {"ok": True, **usersmod.register(BASE_DIR, r.name, r.phone, r.password)}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/auth/login")
async def auth_login(r: LoginIn):
    try:
        return {"ok": True, **usersmod.login(BASE_DIR, r.phone, r.password)}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/auth/me")
async def auth_me(request: Request):
    u = usersmod.me_by_token(BASE_DIR, _bearer(request))
    if not u:
        raise HTTPException(401, "Avval kiring")
    return u

@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    usersmod.logout(BASE_DIR, _bearer(request))
    return {"ok": True}

@app.get("/api/orders/mine")
async def my_orders(request: Request):
    u = usersmod.me_by_token(BASE_DIR, _bearer(request))
    if not u:
        raise HTTPException(401, "Avval kiring")
    return [o for o in load_orders()[::-1] if o.get("user_id") == u["id"]][:20]

@app.get("/api/orders/track")
async def track_order(order_id: int, phone: str):
    ph = usersmod.norm_phone(phone)
    for o in load_orders():
        if o.get("id") == order_id and usersmod.norm_phone(o.get("phone", "")) == ph:
            return o
    raise HTTPException(404, "Buyurtma topilmadi")

# --- pages ---
@app.get("/about")
async def page_about():
    return page("about.html")

@app.get("/track")
async def page_track():
    return page("track.html")

@app.get("/cabinet")
async def page_cabinet():
    return page("cabinet.html")

@app.get("/shop")
async def page_shop():
    return page("shop.html")

@app.get("/sale")
async def page_sale():
    return page("sale.html")

@app.get("/product/{slug}")
async def page_product(slug: str):
    return page("product.html")

@app.get("/wishlist")
async def page_wishlist():
    return page("wishlist.html")

@app.get("/checkout")
async def page_checkout():
    return page("checkout.html")

@app.get("/contact")
async def page_contact():
    return page("contact.html")

# --- frontend ---
@app.get("/")
async def index():
    return page("index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
