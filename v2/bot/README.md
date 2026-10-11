# FAX Flores v2 bot (Django API ustida)

Jonli v1 botga tegilmaydi. Bu bot v2 backend tayyor bo'lganda (VPS) ishga tushadi.

## Sozlash

```powershell
$env:BOT_TOKEN="123456:ABC..."
$env:ADMIN_IDS="111111,222222"
$env:V2_API="http://127.0.0.1:8000/api/v2"
$env:V2_TOKEN="<admin tokeni>"
py -3 bot.py
```

Staff token olish:
```powershell
py -3 ..\manage.py shell -c "from django.contrib.auth.models import User; from rest_framework.authtoken.models import Token; u=User.objects.get(username='admin'); print(Token.objects.get_or_create(user=u)[0].key)"
```

Linux (systemd):
```ini
[Unit]
Description=faxbot
After=network.target
[Service]
WorkingDirectory=/opt/azaflowers/v2/bot
Environment=BOT_TOKEN=... ADMIN_IDS=... V2_API=http://127.0.0.1:8000/api/v2 V2_TOKEN=...
ExecStart=/usr/bin/python3 bot.py
Restart=always
[Install]
WantedBy=multi-user.target
```

## Test

```powershell
py -3 tests.py
```

## Funksiyalar

Admin: /start panel, /orders (filtr+sahifa), holat tugmalari, /stats,
/products + /delproduct, /addproduct (7 qadamli tugmali wizard, foto yuklash),
/promo_add/list/del, /setcard, /card, /help.
Mijoz: /start ord_ID (bog'lash + to'lov yo'riqnomasi), chek foto/hujjat yuborish
(avtomatik v2 ga yuklanadi + adminlarga forward), /myorders + ✅ Qabul qildim.
