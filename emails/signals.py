import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models.Customer import Customer
from shop.models.Order import Order
from emails.utils import (
    send_admin_new_order,
    send_order_confirmation,
    send_order_status_update,
    send_welcome_email,
)


@receiver(pre_save, sender=Order)
def capture_old_order_status(sender, instance, **kwargs):
    """Mémorise l'ancien statut avant la sauvegarde pour détecter les changements."""
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """Envoie les emails selon la situation (nouvelle commande ou changement de statut)."""
    try:
        if created:
            send_order_confirmation(instance)
            send_admin_new_order(instance)
        else:
            old_status = getattr(instance, '_old_status', None)
            if old_status is not None and old_status != instance.status:
                send_order_status_update(instance)
    except Exception as e:
        logger.error(f'Erreur signal order_post_save (commande #{instance.pk}) : {e}')


@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    """Envoie un email de bienvenue aux nouveaux clients (pas aux staff/superusers)."""
    try:
        if created and not instance.is_staff and not instance.is_superuser:
            if instance.email:
                send_welcome_email(instance)
    except Exception as e:
        logger.error(f'Erreur signal customer_post_save (user #{instance.pk}) : {e}')
