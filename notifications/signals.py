import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models.Order import Order
from shop.models.Product import Product
from accounts.models.Customer import Customer

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def notify_new_order(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from notifications.tasks import task_notify_new_order
        task_notify_new_order.delay(instance.pk)
    except Exception as e:
        logger.error(f"notify_new_order échoué pour commande #{instance.pk} : {e}")


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    if created:
        return
    old_status = getattr(instance, "_old_status", None)
    if old_status is None or old_status == instance.status:
        return
    try:
        from notifications.tasks import task_notify_order_status
        task_notify_order_status.delay(instance.pk, instance.status)
    except Exception as e:
        logger.error(f"notify_order_status_change échoué pour commande #{instance.pk} : {e}")


@receiver(post_save, sender=Order)
def notify_proof_submitted(sender, instance, created, **kwargs):
    if created:
        return
    old_payment = getattr(instance, "_old_payment_status", None)
    if old_payment != "unpaid" or instance.payment_status != "proof_submitted":
        return
    try:
        from notifications.tasks import task_notify_proof_submitted
        task_notify_proof_submitted.delay(instance.pk)
    except Exception as e:
        logger.error(f"notify_proof_submitted échoué pour commande #{instance.pk} : {e}")


@receiver(post_save, sender=Order)
def notify_payment_verified(sender, instance, created, **kwargs):
    if created:
        return
    old_payment = getattr(instance, "_old_payment_status", None)
    if old_payment != "proof_submitted" or instance.payment_status != "verified":
        return
    try:
        from notifications.tasks import task_notify_payment_verified
        task_notify_payment_verified.delay(instance.pk)
    except Exception as e:
        logger.error(f"notify_payment_verified échoué pour commande #{instance.pk} : {e}")


@receiver(post_save, sender=Customer)
def notify_admin_new_customer(sender, instance, created, **kwargs):
    if not created or instance.is_staff or instance.is_superuser:
        return
    try:
        from notifications.tasks import task_notify_new_customer
        task_notify_new_customer.delay(instance.pk)
    except Exception as e:
        logger.error(f"notify_admin_new_customer échoué pour customer #{instance.pk} : {e}")


@receiver(post_save, sender=Product)
def notify_new_product(sender, instance, created, **kwargs):
    if not created or not instance.is_available:
        return
    try:
        from notifications.tasks import task_notify_new_product
        task_notify_new_product.delay(instance.pk)
    except Exception as e:
        logger.error(f"notify_new_product échoué pour produit #{instance.pk} : {e}")
