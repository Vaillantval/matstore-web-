from django import template
from django.core.cache import cache

register = template.Library()

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'HTG': 'G',
    'CAD': 'CA$',
    'CHF': 'CHF',
    'JPY': '¥',
    'MAD': 'MAD',
    'XOF': 'FCFA',
    'DZD': 'DA',
    'TND': 'DT',
    'BRL': 'R$',
    'MXN': 'MX$',
}

# Devises sans décimales
NO_DECIMAL_CURRENCIES = {'JPY', 'XOF'}


def _get_setting():
    """Retourne le Setting depuis le cache ou la DB."""
    setting = cache.get('shop_setting')
    if setting is None:
        from shop.models.Setting import Setting
        setting = Setting.objects.first()
        cache.set('shop_setting', setting, 300)  # 5 min
    return setting


def _get_rate(base, target):
    """Retourne le taux de conversion depuis le cache ou la DB."""
    if base == target:
        return 1.0
    cache_key = f'rate_{base}_{target}'
    rate = cache.get(cache_key)
    if rate is None:
        from shop.models.ExchangeRate import ExchangeRate
        obj = ExchangeRate.objects.filter(
            base_currency=base, target_currency=target
        ).first()
        rate = obj.rate if obj else 1.0
        cache.set(cache_key, rate, 3600)  # 1 heure
    return rate


def _format(amount, currency):
    """Formate le montant avec le symbole de la devise."""
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in NO_DECIMAL_CURRENCIES:
        formatted = f"{int(round(amount)):,}".replace(',', ' ')
    else:
        formatted = f"{amount:,.2f}".replace(',', ' ')
    # Symbole avant ou après selon la devise
    if currency in ('EUR', 'HTG', 'MAD', 'XOF', 'DZD', 'TND'):
        return f"{formatted} {symbol}"
    return f"{symbol} {formatted}"


@register.filter(name='price_convert')
def price_convert(price):
    """
    Convertit et formate un prix depuis la devise de base vers la devise d'affichage.
    Usage : {{ product.solde_price|price_convert }}
    """
    try:
        price = float(price)
    except (TypeError, ValueError):
        return price

    setting = _get_setting()
    if setting is None:
        return f"{price:.2f}"

    base = setting.base_currency
    target = setting.currency

    rate = _get_rate(base, target)
    converted = price * rate

    return _format(converted, target)


@register.filter(name='price_in')
def price_in(price, currency):
    """
    Convertit un prix vers une devise spécifique (depuis la base_currency du Setting).
    Usage : {{ product.solde_price|price_in:'USD' }}
    """
    try:
        price = float(price)
    except (TypeError, ValueError):
        return price

    setting = _get_setting()
    if setting is None:
        return f"{price:.2f}"

    base = setting.base_currency
    rate = _get_rate(base, currency)
    converted = price * rate
    return _format(converted, currency)


@register.filter(name='discount_percent')
def discount_percent(solde_price, regular_price):
    """
    Calcule le pourcentage de réduction entre regular_price et solde_price.
    Usage : {{ product.solde_price|discount_percent:product.regular_price }}
    Retourne un entier (ex: 25) ou None si pas de réduction.
    """
    try:
        solde = float(solde_price)
        regular = float(regular_price)
    except (TypeError, ValueError):
        return None
    if regular <= 0 or solde >= regular:
        return None
    return round((regular - solde) / regular * 100)


@register.simple_tag
def currency_symbol():
    """Retourne le symbole de la devise d'affichage. Usage : {% currency_symbol %}"""
    setting = _get_setting()
    if setting is None:
        return ''
    return CURRENCY_SYMBOLS.get(setting.currency, setting.currency)


@register.simple_tag
def display_currency():
    """Retourne le code de la devise d'affichage. Usage : {% display_currency %}"""
    setting = _get_setting()
    if setting is None:
        return ''
    return setting.currency
