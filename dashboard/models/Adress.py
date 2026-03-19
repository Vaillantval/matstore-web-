from django.db import models

from accounts.models import Customer


class Adress(models.Model):
    ADRESS_TYPE_CHOICES = [("billing", "Billing"), ("shipping", "Shipping")]
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    code_postal = models.CharField(max_length=10)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, null=True, blank=True)
    more_details = models.TextField(max_length=500, null=True, blank=True)
    author = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="adresses",
        null=True,
        blank=True,
    )
    adress_type = models.CharField(max_length=255, choices=ADRESS_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_adress_as_string(self):
        adress_parts = [
            self.name,
            self.full_name,
            self.street,
            f"{self.code_postal} {self.city}",
            self.country,
            self.phone,
        ]
        return ", ".join(filter(None, adress_parts))
