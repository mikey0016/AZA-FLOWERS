from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from apps.accounts.models import Address, CustomerProfile, norm_phone
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=80)
    phone = serializers.CharField(min_length=7, max_length=20)
    password = serializers.CharField(min_length=4, max_length=64, write_only=True)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ["name", "phone"]
        read_only_fields = ["phone"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "label", "region", "city", "address", "note", "is_default"]


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = norm_phone(ser.validated_data["phone"])
        if len(phone) < 9:
            return Response({"ok": False, "error": "Telefon noto'g'ri"},
                            status=status.HTTP_400_BAD_REQUEST)
        if CustomerProfile.objects.filter(phone=phone).exists():
            return Response({"ok": False, "error": "Bu raqam band"},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=phone,
                                        password=ser.validated_data["password"])
        CustomerProfile.objects.create(user=user, name=ser.validated_data["name"].strip(),
                                       phone=phone)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"ok": True, "token": token.key,
                         "user": {"name": user.profile.name, "phone": phone}},
                        status=status.HTTP_201_CREATED)


class LoginView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        phone = norm_phone(ser.validated_data["phone"])
        user = authenticate(username=phone, password=ser.validated_data["password"])
        if not user:
            return Response({"ok": False, "error": "Telefon yoki parol xato"},
                            status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        name = getattr(getattr(user, "profile", None), "name", phone)
        return Response({"ok": True, "token": token.key,
                         "user": {"name": name, "phone": phone}})


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyOrdersView(generics.ListAPIView):
    """Kirishgan mijozning o'z telefonidagi buyurtmalari."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        try:
            phone = self.request.user.profile.phone
        except CustomerProfile.DoesNotExist:
            return Order.objects.none()
        return (Order.objects.select_related("payment")
                .prefetch_related("items", "history")
                .filter(phone__contains=phone[-9:]).order_by("-id")[:20])
