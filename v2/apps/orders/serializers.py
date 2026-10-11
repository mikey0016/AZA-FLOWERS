from rest_framework import serializers
from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["product_slug", "name", "price", "qty", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    history = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "no", "name", "phone", "region", "city", "address", "note",
                  "lat", "lon", "ship_method", "ship_fee", "pay_method",
                  "subtotal", "discount", "total", "status", "items", "history",
                  "remaining", "payment", "created_at"]

    def get_payment(self, o):
        try:
            p = o.payment
        except Exception:
            return None
        data = {"id": p.pk, "method": p.method, "required_amount": str(p.required_amount),
                "received": str(p.received), "remaining": str(p.remaining),
                "status": p.status}
        if p.method == "card":
            from apps.payments.models import PaymentSettings
            s = PaymentSettings.current()
            data["cardholder"] = s.cardholder
            data["card_number"] = s.card_number
            data["instructions"] = s.instructions_uz
        return data

    def get_history(self, o):
        return [{"from": h.from_status, "to": h.to_status, "by": h.by,
                 "at": h.created_at} for h in o.history.all()]

    def get_remaining(self, o):
        try:
            return str(o.payment.remaining)
        except Exception:
            return str(o.total)


class OrderCreateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=80)
    phone = serializers.CharField(min_length=7, max_length=20)
    region = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField(required=False, allow_blank=True, default="")
    address = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    lat = serializers.FloatField(required=False, allow_null=True, default=None)
    lon = serializers.FloatField(required=False, allow_null=True, default=None)
    ship = serializers.ChoiceField(choices=["standard", "express"], default="standard")
    pay = serializers.ChoiceField(choices=["cash", "card"], default="cash")
    promo = serializers.CharField(required=False, allow_blank=True, default="")
    client_key = serializers.CharField(required=False, allow_blank=True, default="")
    tg_user = serializers.IntegerField(required=False, allow_null=True, default=None)
    items = serializers.ListField(
        child=serializers.DictField(), min_length=1, max_length=50)


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[c[0] for c in Order.STATUS_CHOICES])
    by = serializers.CharField(required=False, allow_blank=True, default="")
