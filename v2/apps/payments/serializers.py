from rest_framework import serializers
from apps.payments.models import Coupon, Payment, PaymentEvent, PaymentReceipt, PaymentSettings


class PaymentSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSettings
        fields = ["cardholder", "card_number", "instructions_uz", "instructions_ru",
                  "cash_enabled", "cash_advance_pct", "card_advance_pct"]
        extra_kwargs = {"card_number": {"write_only": False}}


class PaymentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentEvent
        fields = ["id", "kind", "amount", "by", "reason", "created_at"]


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = ["id", "file", "reference", "status", "uploaded_at",
                  "reviewed_by", "reviewed_at", "reject_reason"]
        read_only_fields = ["status", "reviewed_by", "reviewed_at", "reject_reason"]


class PaymentSerializer(serializers.ModelSerializer):
    order_no = serializers.CharField(source="order.no", read_only=True)
    order_total = serializers.DecimalField(source="order.total", max_digits=14,
                                           decimal_places=2, read_only=True)
    remaining = serializers.ReadOnlyField()
    events = PaymentEventSerializer(many=True, read_only=True)
    receipts = ReceiptSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "order", "order_no", "order_total", "method", "required_amount",
                  "received", "remaining", "status", "events", "receipts", "updated_at"]
        read_only_fields = ["order", "method", "required_amount", "received", "status"]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["id", "code", "pct", "max_uses", "used", "active", "created_at"]


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    by = serializers.CharField(required=False, allow_blank=True, default="")


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3, max_length=300)
    by = serializers.CharField(required=False, allow_blank=True, default="")
