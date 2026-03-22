import logging

from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models.Customer import Customer
from shop.models.Order import Order
from shop.models.Setting import Setting
from emails.utils import (
    send_admin_new_order,
    send_order_confirmation,
    send_order_status_update,
    send_proof_submitted_notification,
    send_welcome_email,
)


@receiver(pre_save, sender=Order)
def capture_old_order_status(sender, instance, **kwargs):
    """Mémorise l'ancien statut et payment_status avant la sauvegarde."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_payment_status = old.payment_status
        except sender.DoesNotExist:
            instance._old_status = None
            instance._old_payment_status = None
    else:
        instance._old_status = None
        instance._old_payment_status = None


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

            old_payment_status = getattr(instance, '_old_payment_status', None)
            if (
                old_payment_status is not None
                and old_payment_status != instance.payment_status
                and instance.payment_status == 'proof_submitted'
            ):
                send_proof_submitted_notification(instance)
    except Exception as e:
        logger.error(f'Erreur signal order_post_save (commande #{instance.pk}) : {e}')


@receiver(post_save, sender=Setting)
def setting_post_save(sender, instance, **kwargs):
    """Invalide le cache du Setting dès qu'il est modifié en admin."""
    cache.delete('shop_setting')


@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    """Envoie un email de bienvenue aux nouveaux clients (pas aux staff/superusers)."""
    try:
        if created and not instance.is_staff and not instance.is_superuser:
            if instance.email:
                send_welcome_email(instance)
    except Exception as e:
        logger.error(f'Erreur signal customer_post_save (user #{instance.pk}) : {e}')
