# FAX Flores v2 — Django backend (1-faza: do'kon + buyurtma + qo'lda to'lov + admin)

Jonli v1 (FastAPI) ga tegilmaydi. v2 alohida papkada rivojlanadi.

## Tez ishga tushirish (Windows PowerShell)

```powershell
cd C:\Users\ASUS\PycharmProjects\AZA-FLOWERS
py -3 -m pip install -r v2/requirements.txt
py -3 v2/manage.py migrate
py -3 v2/manage.py import_v1          # v1 JSON ma'lumotlar (ixtiyoriy, idempotent)
py -3 v2/manage.py createsuperuser    # admin login
py -3 v2/manage.py test apps.orders apps.payments
py -3 v2/manage.py runserver          # http://127.0.0.1:8000/admin/
```

## Frontend (Next.js mijoz vitrinasi)

```powershell
cd v2/frontend
npm install
npm run dev                        # http://127.0.0.1:3000 (API: 8000 dagi Django)
npm run build                      # production tekshiruvi
```

`API_URL` env (server tomonda) backend manzilini beradi, brauzerda `/api/v2/*`
so'rovlar Next.js rewrite orqali Django'ga proksilanadi (CORS muammosi yo'q).
Sahifalar: `/`, `/shop`, `/product/[slug]`, `/wishlist`, `/checkout`,
`/track`, `/about`, `/contact`. UZ/RU almashtirgich header'da.

Linux:
```bash
python3 -m pip install -r v2/requirements.txt
python3 v2/manage.py migrate
python3 v2/manage.py runserver
```

## Muhit (.env)

`v2/.env.example` ni `v2/.env` ga nusxalang. Standart SQLite ishlaydi.
PostgreSQL uchun `POSTGRES_DB/USER/PASSWORD/HOST` ni to'ldiring
(`psycopg` ni requirements'dan yoqing) va `migrate` qiling.

## API (v2)

Ochiq:
- `GET /api/v2/shop/categories/`, `GET /api/v2/shop/products/?category=&q=&sort=&featured=`
- `GET /api/v2/shop/products/<slug>/`
- `POST /api/v2/orders/` — buyurtma (narxlar serverda hisoblanadi, `client_key` dublikatdan himoya)
- `GET /api/v2/orders/<id>/?phone=...` — mehmon kuzatuvi
- `POST /api/v2/receipts/` — chek yuklash (`payment_id`, `phone`, `file`)

Xodimlar (Basic/Session auth, `is_staff` shart):
- `GET /api/v2/staff/orders/?status=&pay_method=&q=` + `POST .../set_status/`
- `GET /api/v2/staff/payments/?status=&method=&q=`
- `POST .../confirm_advance/ | confirm_card | reject_receipt | record_cash`
- `GET/PUT /api/v2/staff/payment-settings/`, `CRUD /api/v2/staff/coupons/`
- Django admin: `/admin/` — mahsulot, buyurtma, to'lov, chek, promokod, sozlama

## To'lov qoidalari (50/100)

- Naqd: jami × 50% oldindan, qolgani yetkazishda naqd.
- Karta: 100% oldindan karta o'tkazmasi, admin tasdiqlaydi.
- `advance + remaining == total` (ROUND_HALF_UP).
- Chek yuklash HECH QACHON avtomatik to'langan deb belgilamaydi.
- Har bir moliyaviy harakat `PaymentEvent` ga yoziladi (kim/qachon/nima).
- Zaxira `preparing` ga o'tishda atomar kamayadi (oversell yo'q).

## Keyingi fazalar (reja)

2. ~~Next.js mijoz frontend~~ — TAYYOR (`v2/frontend`: home/shop/product/wishlist/checkout/track, UZ/RU).
3. ~~Botni v2 ga ulash~~ — TAYYOR (`v2/bot`: admin+mijoz, testlar bilan).
4. MinIO toggle + Docker Compose — TAYYOR. Qolgan: VPS + DNS cutover.

## VPS deploy

```bash
# 1. VPS (Ubuntu 24.04, kamida 2GB RAM) + DNS A-record -> server IP
# 2. Docker: curl -fsSL https://get.docker.com | sh
git clone <repo> && cd AZA-FLOWERS/v2
cp .env.example .env   # to'ldiring: DOMAIN, POSTGRES_PASSWORD, SECRETlar
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
```

Nginx/Caddy: `DOMAIN` -> :3000 (frontend); `/api/v2/*`, `/admin/*` -> backend:8000.
SSL: Caddy avtomatik (yoki certbot). MinIO console `:9001` — `azaflowers` bucket (private).
Zaxira (cron): `docker compose exec db pg_dump -U aza azaflowers > backup.sql`.

## Xavfsizlik eslatma

- `DEBUG=False`, kuchli `SECRET_KEY`, HTTPS — production'da shart.
- `card_number` faqat admin panelda ko'rinadi, mijozga faqat to'lov yo'riqnomasida.
- Cheklar `media/` da (dev) — production'da privat MinIO bucket + imzolangan URL.
