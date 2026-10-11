# AZA FLOWERS v2 — Django backend (1-faza: do'kon + buyurtma + qo'lda to'lov + admin)

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

2. Next.js mijoz frontend (katalog, savat, checkout, tracking, UZ/RU).
3. Telegram botni v2 API ga ulash (xabarlar, chek, tasdiqlash).
4. MinIO (rasmlar + privat cheklar), Docker Compose, VPS deploy.
5. Kupon/loyallik kengaytmasi, hisobotlar, audit jurnali UI.

## Xavfsizlik eslatma

- `DEBUG=False`, kuchli `SECRET_KEY`, HTTPS — production'da shart.
- `card_number` faqat admin panelda ko'rinadi, mijozga faqat to'lov yo'riqnomasida.
- Cheklar `media/` da (dev) — production'da privat MinIO bucket + imzolangan URL.
