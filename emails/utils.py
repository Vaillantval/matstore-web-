import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    'pending': 'En attente',
    'processing': 'En cours de traitement',
    'shipped': 'Expédiée',
    'delivered': 'Livrée',
    'canceled': 'Annulée',
}

STATUS_MESSAGES = {
    'pending': 'Votre commande est en attente de traitement.',
    'processing': 'Votre commande est en cours de traitement par notre équipe.',
    'shipped': 'Bonne nouvelle ! Votre commande a été expédiée et est en route vers vous.',
    'delivered': 'Votre commande a été livrée avec succès. Merci pour votre confiance !',
    'canceled': "Votre commande a malheureusement été annulée. Contactez-nous pour plus d'informations.",
}


def send_order_confirmation(order):
    """Email de confirmation envoyé au client après une nouvelle commande."""
    try:
        context = {
            'order': order,
            'details': order.order_details.all(),
            'site_url': settings.SITE_URL,
        }
        subject = f'Confirmation de votre commande #{order.id} - MatStore Haiti'
        html_content = render_to_string('emails/order_confirmation.html', context)
        text_content = (
            f'Commande #{order.id} confirmée. '
            f'Total : {order.order_cost_ttc} HTG. '
            f'Suivi : {settings.SITE_URL}/dashboard/orders/'
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.author.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
    except Exception as e:
        logger.error(f'Email de confirmation non envoyé pour commande #{order.id} : {e}')


def send_admin_new_order(order):
    """Email de notification envoyé à l'admin pour chaque nouvelle commande."""
    try:
        context = {
            'order': order,
            'details': order.order_details.all(),
            'site_url': settings.SITE_URL,
            'admin_url': f'{settings.SITE_URL}/admin/shop/order/{order.id}/change/',
        }
        subject = f'Nouvelle commande #{order.id} — {order.client_name}'
        html_content = render_to_string('emails/admin_new_order.html', context)
        text_content = (
            f'Nouvelle commande #{order.id} de {order.client_name}. '
            f'Total : {order.order_cost_ttc} HTG.'
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMINS_NOTIFY],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
    except Exception as e:
        logger.error(f'Email admin non envoyé pour commande #{order.id} : {e}')


def send_order_status_update(order):
    """Email envoyé au client quand le statut de sa commande change."""
    try:
        context = {
            'order': order,
            'status_label': STATUS_LABELS.get(order.status, order.status),
            'status_message': STATUS_MESSAGES.get(order.status, ''),
            'site_url': settings.SITE_URL,
        }
        subject = f'Mise à jour de votre commande #{order.id} - MatStore Haiti'
        html_content = render_to_string('emails/order_status_update.html', context)
        text_content = (
            f'Commande #{order.id} : {STATUS_LABELS.get(order.status, order.status)}. '
            f'{STATUS_MESSAGES.get(order.status, "")}'
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.author.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
    except Exception as e:
        logger.error(f'Email de statut non envoyé pour commande #{order.id} : {e}')


def send_welcome_email(user):
    """Email de bienvenue envoyé au client après son inscription."""
    try:
        context = {
            'user': user,
            'site_url': settings.SITE_URL,
            'login_url': f'{settings.SITE_URL}/accounts/connexion/',
        }
        subject = 'Bienvenue chez MatStore Haiti !'
        html_content = render_to_string('emails/welcome.html', context)
        text_content = (
            f'Bienvenue {user.first_name or user.username} ! '
            f'Votre compte MatStore Haiti est créé. '
            f'Identifiant : {user.email}'
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
    except Exception as e:
        logger.error(f'Email de bienvenue non envoyé pour {user.username} : {e}')
