from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.orders.serializers import OrderCreateSerializer, OrderSerializer, OrderStatusSerializer
from apps.orders.services import OrderError, create_order, set_order_status


class PublicOrderCreate(generics.CreateAPIView):
    """Ochiq buyurtma yaratish (guest checkout). Narxlar serverda hisoblanadi."""
    permission_classes = [permissions.AllowAny]
    serializer_class = OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = create_order(ser.validated_data, by="site")
        except OrderError as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        pay = order.payment
        bot_url = None
        if order.tg_user:
            bot_url = None
        return Response({
            "ok": True, "id": order.id, "no": order.no, "total": str(order.total),
            "prepay": str(pay.required_amount), "status": order.status,
            "payment_id": pay.pk, "pay_method": order.pay_method,
        }, status=status.HTTP_201_CREATED)


class PublicOrderTrack(generics.RetrieveAPIView):
    """Mehmon kuzatuvi: id + telefon raqam talab qilinadi."""
    permission_classes = [permissions.AllowAny]
    serializer_class = OrderSerializer

    def get_object(self):
        from django.http import Http404
        try:
            o = Order.objects.select_related("payment").prefetch_related("items", "history").get(pk=self.kwargs["pk"])
        except Order.DoesNotExist:
            raise Http404
        phone = "".join(ch for ch in str(self.request.query_params.get("phone", "")) if ch.isdigit())
        if not phone or phone not in o.phone:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Telefon mos kelmadi")
        return o


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Xodimlar uchun: ro'yxat + batafsil + holat o'tkazish. Faqat staff."""
    queryset = Order.objects.select_related("payment").prefetch_related("items", "history").all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("pay_method"):
            qs = qs.filter(pay_method=p["pay_method"])
        if p.get("q"):
            qs = qs.filter(no__icontains=p["q"]) | qs.filter(phone__icontains=p["q"])
        return qs.distinct()

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        ser = OrderStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = set_order_status(self.get_object(), ser.validated_data["status"],
                                     ser.validated_data.get("by", str(request.user)))
        except OrderError as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "status": order.status})


class BotPendingView(generics.ListAPIView):
    """Bot uchun: to'lov kutilayotgan buyurtmalar (chek + xarita bilan). Staff only."""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (Order.objects.select_related("payment").prefetch_related("items").filter(
            status__in=[Order.STATUS_AWAITING_PAYMENT, Order.STATUS_AWAITING_VERIFY])
            .order_by("-id")[:20])


class GeoReverseView(APIView):
    """Xarita nuqtasi -> manzil (Nominatim proksiysi, kesh bilan)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat", ""))
            lon = float(request.query_params.get("lon", ""))
        except (TypeError, ValueError):
            return Response({"ok": False, "error": "Koordinata xato"},
                            status=status.HTTP_400_BAD_REQUEST)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return Response({"ok": False, "error": "Koordinata xato"},
                            status=status.HTTP_400_BAD_REQUEST)
        from apps.orders.geocode import reverse_geocode
        try:
            return Response(reverse_geocode(lat, lon))
        except Exception:
            return Response({"ok": False, "error": "Topilmadi"})


class BotLinkView(APIView):
    """Mijoz chat_id ni buyurtmaga bog'lash (/start ord_ID). Staff only."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        try:
            order = Order.objects.get(pk=int(request.data.get("order_id")))
        except (Order.DoesNotExist, TypeError, ValueError):
            return Response({"ok": False, "error": "Buyurtma topilmadi"},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            order.tg_user = int(request.data.get("tg_user"))
        except (TypeError, ValueError):
            return Response({"ok": False, "error": "tg_user noto'g'ri"},
                            status=status.HTTP_400_BAD_REQUEST)
        order.save(update_fields=["tg_user", "updated_at"])
        return Response({"ok": True, "id": order.id})
