from django.db import models
from slugify import slugify

from shop.models.Category import Category


class Product(models.Model):
    name = models.CharField(max_length=60, blank=False, null=False)
    slug = models.SlugField(max_length=255, blank=False, null=False)
    description = models.CharField(max_length=120, blank=False, null=False)
    more_description = models.TextField(blank=True, null=True)
    #   image = models.ImageField(blank=True, null=True)
    additional_info = models.CharField(blank=True, null=True)
    stock = models.IntegerField(blank=False, null=False)
    solde_price = models.FloatField(blank=False, null=False)
    regular_price = models.FloatField(blank=False, null=False)
    brand = models.CharField(max_length=60, blank=False, null=False)
    is_available = models.BooleanField(blank=False, null=False)
    is_best_seller = models.BooleanField(blank=False, null=False)
    is_featured = models.BooleanField(blank=False, null=False)
    is_new_arrival = models.BooleanField(blank=False, null=False)
    is_special_offer = models.BooleanField(blank=False, null=False)
    categories = models.ManyToManyField(Category, blank=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
