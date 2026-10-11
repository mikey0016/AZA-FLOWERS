"""v2 prod entry: v1 server.py ga o'xshash (SOCKET yoki PORT).
.env fayldan o'qiydi (pm2 env ga ishonmaydi)."""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

for line in (BASE / ".env").read_text().splitlines() if (BASE / ".env").exists() else []:
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.asgi import get_asgi_application  # noqa: E402

app = get_asgi_application()

if __name__ == "__main__":
    import uvicorn

    sock = os.getenv("SOCKET")
    if sock:
        try:
            if os.path.exists(sock):
                os.unlink(sock)
        except OSError:
            pass
        uvicorn.run(app, uds=sock)
    else:
        uvicorn.run(
            app,
            host=os.getenv("INSTANCE_HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8001")),
        )
