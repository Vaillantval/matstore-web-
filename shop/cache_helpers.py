"""
Fonctions utilitaires avec cache Redis partagées entre les vues.
Chaque helper invalide son cache via shop/signals.py sur post_save du modèle concerné.
"""
from django.core.cache import cache

_CARRIERS_KEY      = 'all_carriers'
_METHODS_KEY       = 'payment_methods'
_COUNTS_KEY        = 'shop_counts'
_EXCHANGE_KEY      = 'exchange_rate_{base}_{target}'

_LONG_TTL  = 3600   # 1h — invalidé par signal
_SHORT_TTL = 300    # 5 min — données plus volatiles


def get_carriers():
    carriers = cache.get(_CARRIERS_KEY)
    if carriers is None:
        from shop.models.Carrier import Carrier
        carriers = list(Carrier.objects.all())
        cache.set(_CARRIERS_KEY, carriers, _LONG_TTL)
    return carriers


def get_payment_methods():
    methods = cache.get(_METHODS_KEY)
    if methods is None:
        from shop.models.Method import Method
        methods = list(Method.objects.filter(is_available=True))
        cache.set(_METHODS_KEY, methods, _LONG_TTL)
    return methods


def get_exchange_rate(base_currency, target_currency):
    key = _EXCHANGE_KEY.format(base=base_currency, target=target_currency)
    rate = cache.get(key)
    if rate is None:
        from shop.models.ExchangeRate import ExchangeRate
        obj = ExchangeRate.objects.filter(
            base_currency=base_currency, target_currency=target_currency
        ).first()
        rate = obj.rate if obj else None
        cache.set(key, rate, _LONG_TTL)
    return rate


def get_shop_counts():
    counts = cache.get(_COUNTS_KEY)
    if counts is None:
        from shop.models import Product, Category
        counts = {
            'product_count':  Product.objects.count(),
            'category_count': Category.objects.count(),
        }
        cache.set(_COUNTS_KEY, counts, _SHORT_TTL)
    return counts


def invalidate_carriers():
    cache.delete(_CARRIERS_KEY)


def invalidate_payment_methods():
    cache.delete(_METHODS_KEY)


def invalidate_exchange_rates():
    try:
        cache.delete_pattern('exchange_rate_*')
    except Exception:
        pass


def invalidate_shop_counts():
    cache.delete(_COUNTS_KEY)
