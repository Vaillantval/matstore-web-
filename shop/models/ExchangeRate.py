from django.db import models


class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=4)
    target_currency = models.CharField(max_length=4)
    rate = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('base_currency', 'target_currency')
        verbose_name = 'Taux de change'
        verbose_name_plural = 'Taux de change'
        ordering = ['base_currency', 'target_currency']

    def __str__(self):
        return f"1 {self.base_currency} = {self.rate} {self.target_currency}"
