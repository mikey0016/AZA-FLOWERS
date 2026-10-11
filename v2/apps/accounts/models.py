from django.contrib.auth.models import User
from django.db import models


def norm_phone(p: str) -> str:
    return "".join(ch for ch in str(p or "") if ch.isdigit())


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self) -> str:
        return f"{self.name} · {self.phone}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=40, default="Uy", blank=True)
    region = models.CharField(max_length=60, blank=True, default="")
    city = models.CharField(max_length=60, blank=True, default="")
    address = models.CharField(max_length=200, blank=True, default="")
    note = models.CharField(max_length=300, blank=True, default="")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-id"]
        verbose_name = "Manzil"
        verbose_name_plural = "Manzillar"

    def __str__(self) -> str:
        return f"{self.label}: {self.city}, {self.address}"[:80]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
