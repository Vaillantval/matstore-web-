import logging
from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models.Customer import Customer
from shop.models.Order import Order
from shop.models.Setting import Setting

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def capture_old_order_status(sender, instance, **kwargs):
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
    try:
        from emails.tasks import (
            task_send_order_confirmation,
            task_send_admin_new_order,
            task_send_order_status_update,
            task_send_proof_submitted,
        )
        if created:
            task_send_order_confirmation.delay(instance.pk)
            task_send_admin_new_order.delay(instance.pk)
        else:
            old_status = getattr(instance, "_old_status", None)
            if old_status is not None and old_status != instance.status:
                task_send_order_status_update.delay(instance.pk)

            old_payment_status = getattr(instance, "_old_payment_status", None)
            if (
                old_payment_status is not None
                and old_payment_status != instance.payment_status
                and instance.payment_status == "proof_submitted"
            ):
                task_send_proof_submitted.delay(instance.pk)
    except Exception as e:
        logger.error(f"Erreur signal order_post_save (commande #{instance.pk}) : {e}")


@receiver(post_save, sender=Setting)
def setting_post_save(sender, instance, **kwargs):
    cache.delete("shop_setting")


@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    try:
        if created and not instance.is_staff and not instance.is_superuser:
            if instance.email:
                from emails.tasks import task_send_welcome_email
                task_send_welcome_email.delay(instance.pk)
    except Exception as e:
        logger.error(f"Erreur signal customer_post_save (user #{instance.pk}) : {e}")
