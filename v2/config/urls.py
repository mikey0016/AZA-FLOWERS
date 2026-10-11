from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path
from pathlib import Path

admin.site.site_header = "FAX Flores — admin"
admin.site.site_title = "FAX Flores"

SPA_DIR = Path(__file__).resolve().parent.parent / "frontend" / "out"


def spa_serve(request, path=""):
    """Next.js static export ni berish (API/admin/mediasiz yo'llar)."""
    if not SPA_DIR.is_dir():
        raise Http404
    target = (SPA_DIR / path) if path else SPA_DIR
    candidates = []
    if path:
        candidates.append(SPA_DIR / path)
        candidates.append(SPA_DIR / (path.rstrip("/") + ".html"))
        candidates.append(SPA_DIR / path.rstrip("/") / "index.html")
    candidates.append(SPA_DIR / "index.html")
    for c in candidates:
        try:
            resolved = c.resolve()
        except OSError:
            continue
        if str(resolved).startswith(str(SPA_DIR.resolve())) and resolved.is_file():
            return FileResponse(open(resolved, "rb"))
    raise Http404


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", include([
        path("", include("apps.shop.urls")),
        path("", include("apps.orders.urls")),
        path("", include("apps.payments.urls")),
        path("", include("apps.accounts.urls")),
    ])),
]

if settings.DEBUG or getattr(settings, "SERVE_MEDIA", False):
    from django.views.static import serve as static_serve
    urlpatterns += [
        path("media/<path:path>", static_serve, {"document_root": settings.MEDIA_ROOT}),
    ]

urlpatterns += [
    path("", spa_serve, {"path": ""}),
    path("<path:path>", spa_serve),
]
