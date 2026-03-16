from django.db import models

CURRENCY_CHOICES = [
    ("HTG", "Gourde haïtienne (HTG)"),
    ("USD", "Dollar américain (USD)"),
    ("EUR", "Euro (EUR)"),
    ("GBP", "Livre sterling (GBP)"),
    ("CAD", "Dollar canadien (CAD)"),
    ("CHF", "Franc suisse (CHF)"),
    ("JPY", "Yen japonais (JPY)"),
    ("MAD", "Dirham marocain (MAD)"),
    ("XOF", "Franc CFA (XOF)"),
    ("DZD", "Dinar algérien (DZD)"),
    ("TND", "Dinar tunisien (TND)"),
    ("BRL", "Real brésilien (BRL)"),
    ("MXN", "Peso mexicain (MXN)"),
]


class Setting(models.Model):
    name = models.CharField(max_length=60, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    base_currency = models.CharField(
        max_length=4,
        choices=CURRENCY_CHOICES,
        default="HTG",
        help_text="Devise dans laquelle les prix des produits sont saisis.",
    )
    currency = models.CharField(
        max_length=4,
        choices=CURRENCY_CHOICES,
        default="HTG",
        help_text="Devise d'affichage sur le site (conversion automatique).",
    )
    taxe_rate = models.FloatField(blank=False, null=False)
    logo = models.ImageField(upload_to="settings/images/", blank=False, null=False)
    street = models.CharField(max_length=60, blank=False, null=False)
    city = models.CharField(max_length=120, blank=False, null=False)
    state = models.CharField(max_length=120, blank=False, null=False)
    code_postal = models.CharField(max_length=60, blank=False, null=False)
    phone = models.CharField(max_length=60, blank=False, null=False)
    email = models.EmailField(blank=False, null=False)
    copyright = models.TextField(blank=False, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
