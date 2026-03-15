"""
Management command pour récupérer les taux de change depuis open.er-api.com (gratuit, sans clé API).
Usage : python manage.py fetch_rates
"""
import urllib.request
import json

from django.core.management.base import BaseCommand
from django.core.cache import cache


API_URL = "https://open.er-api.com/v6/latest/{base}"

TRACKED_CURRENCIES = [
    'HTG', 'USD', 'EUR', 'GBP', 'CAD', 'CHF',
    'JPY', 'MAD', 'XOF', 'DZD', 'TND', 'BRL', 'MXN',
]


def fetch_rates_for_base(base_currency):
    """Appelle l'API et enregistre les taux en DB. Retourne le nombre de taux sauvegardés."""
    from shop.models.ExchangeRate import ExchangeRate

    url = API_URL.format(base=base_currency)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        raise RuntimeError(f"Erreur API ({url}): {e}")

    if data.get('result') != 'success':
        raise RuntimeError(f"Réponse API invalide : {data}")

    rates = data.get('rates', {})
    saved = 0
    for target, rate in rates.items():
        if target in TRACKED_CURRENCIES and target != base_currency:
            ExchangeRate.objects.update_or_create(
                base_currency=base_currency,
                target_currency=target,
                defaults={'rate': rate},
            )
            saved += 1

    # Invalider le cache des taux
    for target in TRACKED_CURRENCIES:
        cache.delete(f'rate_{base_currency}_{target}')
    cache.delete('shop_setting')

    return saved


class Command(BaseCommand):
    help = "Récupère les taux de change depuis open.er-api.com et les met en cache en DB."

    def add_arguments(self, parser):
        parser.add_argument(
            '--base',
            type=str,
            default=None,
            help="Devise de base (ex: HTG). Par défaut : utilise la base_currency du Setting.",
        )

    def handle(self, *args, **options):
        from shop.models.Setting import Setting

        base = options.get('base')
        if not base:
            setting = Setting.objects.first()
            if not setting:
                self.stderr.write(self.style.ERROR(
                    "Aucun Setting trouvé. Créez-en un dans l'admin ou passez --base=HTG"
                ))
                return
            base = setting.base_currency

        self.stdout.write(f"Récupération des taux depuis open.er-api.com pour {base}...")
        try:
            count = fetch_rates_for_base(base)
            self.stdout.write(self.style.SUCCESS(
                f"OK - {count} taux sauvegardes pour {base}."
            ))
        except RuntimeError as e:
            self.stderr.write(self.style.ERROR(str(e)))
