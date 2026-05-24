import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_send_order_confirmation(self, order_id):
    try:
        from shop.models.Order import Order
        from emails.utils import send_order_confirmation
        order = Order.objects.select_related("author").prefetch_related("order_details").get(pk=order_id)
        send_order_confirmation(order)
    except Exception as exc:
        logger.error(f"task_send_order_confirmation échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_send_admin_new_order(self, order_id):
    try:
        from shop.models.Order import Order
        from emails.utils import send_admin_new_order
        order = Order.objects.select_related("author").prefetch_related("order_details").get(pk=order_id)
        send_admin_new_order(order)
    except Exception as exc:
        logger.error(f"task_send_admin_new_order échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_send_order_status_update(self, order_id):
    try:
        from shop.models.Order import Order
        from emails.utils import send_order_status_update
        order = Order.objects.select_related("author").get(pk=order_id)
        send_order_status_update(order)
    except Exception as exc:
        logger.error(f"task_send_order_status_update échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_send_proof_submitted(self, order_id):
    try:
        from shop.models.Order import Order
        from emails.utils import send_proof_submitted_notification
        order = Order.objects.select_related("author").get(pk=order_id)
        send_proof_submitted_notification(order)
    except Exception as exc:
        logger.error(f"task_send_proof_submitted échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_send_welcome_email(self, customer_id):
    try:
        from accounts.models.Customer import Customer
        from emails.utils import send_welcome_email
        customer = Customer.objects.get(pk=customer_id)
        send_welcome_email(customer)
    except Exception as exc:
        logger.error(f"task_send_welcome_email échoué pour customer #{customer_id} : {exc}")
        raise self.retry(exc=exc)
