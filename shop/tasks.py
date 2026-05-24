import logging
from celery import shared_task

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 5          # seuil de stock bas
LOW_STOCK_CACHE_KEY = 'low_stock_alert_sent'
LOW_STOCK_CACHE_TTL = 4 * 3600  # ne pas re-alerter avant 4h


# ── 1. Refresh des taux de change ─────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def task_refresh_exchange_rates(self):
    try:
        from shop.models.Setting import Setting
        from shop.management.commands.fetch_rates import fetch_rates_for_base
        setting = Setting.objects.first()
        if not setting:
            logger.warning("task_refresh_exchange_rates : aucun Setting trouvé.")
            return
        count = fetch_rates_for_base(setting.base_currency)
        logger.info(f"Taux de change rafraîchis : {count} taux pour {setting.base_currency}.")
    except Exception as exc:
        logger.error(f"task_refresh_exchange_rates échoué : {exc}")
        raise self.retry(exc=exc)


# ── 2. Rapport hebdomadaire des ventes → admins ───────────────────────────────

@shared_task
def task_weekly_sales_report():
    try:
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Sum, Count, Q
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from shop.models.Order import Order
        from shop.models.OrderDetail import OrderDetail
        from accounts.models.Customer import Customer

        now   = timezone.now()
        start = now - timedelta(days=7)

        orders = Order.objects.filter(created_at__gte=start)
        total_orders   = orders.count()
        total_revenue  = orders.aggregate(t=Sum('order_cost_ttc'))['t'] or 0
        paid_revenue   = orders.filter(is_paid=True).aggregate(t=Sum('order_cost_ttc'))['t'] or 0

        # Répartition par statut
        by_status = {
            s: orders.filter(status=s).aggregate(n=Count('id'), rev=Sum('order_cost_ttc'))
            for s in ['pending', 'processing', 'shipped', 'delivered', 'canceled']
        }

        # Répartition par méthode de paiement
        by_method = {}
        for o in orders.values('payment_method').annotate(n=Count('id'), rev=Sum('order_cost_ttc')):
            by_method[o['payment_method']] = {'n': o['n'], 'rev': o['rev'] or 0}

        # Top 5 produits (par quantité vendue)
        top_products = (
            OrderDetail.objects
            .filter(order__created_at__gte=start)
            .values('product_name')
            .annotate(qty=Sum('quantity'), revenue=Sum('sub_total_ttc'))
            .order_by('-qty')[:5]
        )

        # Nouveaux clients
        new_customers = Customer.objects.filter(date_joined__gte=start).count()

        context = {
            'start': start,
            'end': now,
            'total_orders': total_orders,
            'total_revenue': round(total_revenue, 2),
            'paid_revenue': round(paid_revenue, 2),
            'by_status': by_status,
            'by_method': by_method,
            'top_products': list(top_products),
            'new_customers': new_customers,
            'site_url': settings.SITE_URL,
        }

        subject = f"📊 Rapport hebdomadaire MatStore — semaine du {start.strftime('%d/%m/%Y')}"
        html_content = render_to_string('emails/weekly_report.html', context)
        text_content = (
            f"Rapport du {start.strftime('%d/%m/%Y')} au {now.strftime('%d/%m/%Y')}\n"
            f"Commandes : {total_orders} | CA total : {round(total_revenue, 2)} HTG | "
            f"CA encaissé : {round(paid_revenue, 2)} HTG | Nouveaux clients : {new_customers}"
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMINS_NOTIFY],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info("Rapport hebdomadaire envoyé.")
    except Exception as exc:
        logger.error(f"task_weekly_sales_report échoué : {exc}")


# ── 3. Alerte stock bas ────────────────────────────────────────────────────────

@shared_task
def task_low_stock_alert():
    try:
        from django.core.cache import cache
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from shop.models.Product import Product

        # Évite de spammer : une alerte max toutes les 4h
        if cache.get(LOW_STOCK_CACHE_KEY):
            return

        low = list(
            Product.objects.filter(
                is_available=True,
                stock__lte=LOW_STOCK_THRESHOLD,
            ).values('name', 'stock').order_by('stock')
        )

        if not low:
            return

        lines = "\n".join(f"  - {p['name']} : {p['stock']} restant(s)" for p in low)
        body = (
            f"{len(low)} produit(s) en stock bas (≤ {LOW_STOCK_THRESHOLD} unités) :\n\n"
            f"{lines}\n\n"
            f"Gérer le stock : {settings.SITE_URL}/admin/shop/product/"
        )
        msg = EmailMultiAlternatives(
            subject=f"⚠️ Stock bas — {len(low)} produit(s) à réapprovisionner",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMINS_NOTIFY],
        )
        msg.send()

        cache.set(LOW_STOCK_CACHE_KEY, True, LOW_STOCK_CACHE_TTL)
        logger.info(f"Alerte stock bas envoyée : {len(low)} produit(s).")
    except Exception as exc:
        logger.error(f"task_low_stock_alert échoué : {exc}")
