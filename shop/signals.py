from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models.Product import Product
from shop.models.Category import Category
from shop.models.Slider import Slider
from shop.models.Collection import Collection
from shop.models.Page import Page
from shop.models.Setting import Setting
from shop.models.Carrier import Carrier
from shop.models.Method import Method
from shop.models.ExchangeRate import ExchangeRate


def _invalidate_home_cache():
    from django.core.cache import cache
    cache.delete('home_context_v2')


def _invalidate_site_settings_cache():
    from django.core.cache import cache
    cache.delete('site_settings_ctx')


@receiver(post_save, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    from django.core.cache import cache
    from shop.views.shop_view import _invalidate_shop_list_cache
    cache.delete(f'product_detail_{instance.slug}')
    _invalidate_shop_list_cache()
    _invalidate_home_cache()


@receiver(post_save, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    from shop.views.shop_view import _invalidate_shop_list_cache
    _invalidate_shop_list_cache()
    _invalidate_site_settings_cache()


@receiver(post_save, sender=Slider)
def invalidate_slider_cache(sender, instance, **kwargs):
    _invalidate_home_cache()


@receiver(post_save, sender=Collection)
def invalidate_collection_cache(sender, instance, **kwargs):
    _invalidate_home_cache()
    _invalidate_site_settings_cache()


@receiver(post_save, sender=Page)
def invalidate_page_cache(sender, instance, **kwargs):
    _invalidate_site_settings_cache()


@receiver(post_save, sender=Setting)
def invalidate_setting_cache(sender, instance, **kwargs):
    _invalidate_site_settings_cache()


@receiver(post_save, sender=Carrier)
def invalidate_carrier_cache(sender, instance, **kwargs):
    from shop.cache_helpers import invalidate_carriers
    invalidate_carriers()


@receiver(post_save, sender=Method)
def invalidate_method_cache(sender, instance, **kwargs):
    from shop.cache_helpers import invalidate_payment_methods
    invalidate_payment_methods()


@receiver(post_save, sender=ExchangeRate)
def invalidate_exchange_rate_cache(sender, instance, **kwargs):
    from shop.cache_helpers import invalidate_exchange_rates
    invalidate_exchange_rates()
