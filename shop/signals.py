from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models.Product import Product
from shop.models.Category import Category
from shop.models.Slider import Slider
from shop.models.Collection import Collection
from shop.models.Page import Page
from shop.models.Setting import Setting


def _invalidate_home_cache():
    from django.core.cache import cache
    cache.delete('home_context')


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
