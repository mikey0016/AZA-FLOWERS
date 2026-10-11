from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.payments.models import Coupon, Payment, PaymentSettings
from apps.payments.serializers import (
    AmountSerializer, CouponSerializer, PaymentSerializer, PaymentSettingsSerializer,
    ReceiptSerializer, RejectSerializer,
)
from apps.payments.services import (
    PaymentError, confirm_advance, confirm_card, record_cash, reject_receipt, submit_receipt,
)


class PaymentSettingsView(generics.RetrieveUpdateAPIView):
    queryset = PaymentSettings.objects.all()
    serializer_class = PaymentSettingsSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        return PaymentSettings.current()


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related("order").prefetch_related("events", "receipts").all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("method"):
            qs = qs.filter(method=p["method"])
        if p.get("q"):
            qs = qs.filter(order__no__icontains=p["q"])
        return qs

    def _do(self, fn, request, *a, **kw):
        try:
            obj = fn(*a, **kw)
        except PaymentError as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "payment": PaymentSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def confirm_advance(self, request, pk=None):
        ser = AmountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._do(confirm_advance, request, self.get_object().pk,
                        ser.validated_data["amount"], ser.validated_data.get("by", str(request.user)))

    @action(detail=True, methods=["post"])
    def confirm_card(self, request, pk=None):
        by = str(request.data.get("by", request.user))
        return self._do(confirm_card, request, self.get_object().pk, by)

    @action(detail=True, methods=["post"])
    def reject_receipt(self, request, pk=None):
        ser = RejectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._do(reject_receipt, request, self.get_object().pk,
                        ser.validated_data["reason"], ser.validated_data.get("by", str(request.user)))

    @action(detail=True, methods=["post"])
    def record_cash(self, request, pk=None):
        ser = AmountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._do(record_cash, request, self.get_object().pk,
                        ser.validated_data["amount"], ser.validated_data.get("by", str(request.user)))


class ReceiptUpload(generics.CreateAPIView):
    """Mijoz chek yuklaydi (order_id + telefon tekshiruvi bilan)."""
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            payment = Payment.objects.select_related("order").get(pk=request.data.get("payment_id"))
        except Payment.DoesNotExist:
            return Response({"ok": False, "error": "To'lov topilmadi"},
                            status=status.HTTP_404_NOT_FOUND)
        phone = "".join(ch for ch in str(request.data.get("phone", "")) if ch.isdigit())
        if not phone or phone not in payment.order.phone:
            return Response({"ok": False, "error": "Telefon mos kelmadi"},
                            status=status.HTTP_403_FORBIDDEN)
        ser = self.get_serializer(data={"file": request.data.get("file"),
                                        "reference": request.data.get("reference", "")})
        ser.is_valid(raise_exception=True)
        try:
            receipt = submit_receipt(payment.pk, ser.validated_data["file"],
                                     ser.validated_data.get("reference", ""))
        except PaymentError as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "receipt": ReceiptSerializer(receipt).data},
                        status=status.HTTP_201_CREATED)


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]


class CouponValidate(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        code = (request.query_params.get("code") or "").strip().upper()
        if not code:
            return Response({"ok": False, "error": "kod kiritilmagan"})
        try:
            c = Coupon.objects.get(code=code, active=True)
        except Coupon.DoesNotExist:
            return Response({"ok": False, "error": "bunday promokod yo'q"})
        if c.max_uses and c.used >= c.max_uses:
            return Response({"ok": False, "error": "promokod tugagan"})
        return Response({"ok": True, "code": c.code, "pct": c.pct})
