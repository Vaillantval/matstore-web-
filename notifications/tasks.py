import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def task_notify_new_order(self, order_id):
    try:
        from shop.models.Order import Order
        from notifications.fcm import TOPIC_ADMIN, send_to_token, send_to_topic
        order = Order.objects.select_related("author").get(pk=order_id)

        token = order.author.fcm_token
        if token:
            send_to_token(
                token=token,
                title="Commande reçue",
                body=f"Votre commande #{order.id} a bien été enregistrée.",
                data={"type": "new_order", "order_id": order.id, "total": order.order_cost_ttc, "status": order.status},
            )
        send_to_topic(
            topic=TOPIC_ADMIN,
            title=f"Nouvelle commande #{order.id}",
            body=f"{order.client_name} — {order.order_cost_ttc} HTG",
            data={"type": "new_order_admin", "order_id": order.id, "client_name": order.client_name, "total": order.order_cost_ttc, "payment_method": order.payment_method},
        )
    except Exception as exc:
        logger.error(f"task_notify_new_order échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def task_notify_order_status(self, order_id, new_status):
    try:
        from shop.models.Order import Order
        from notifications.fcm import send_to_token
        STATUS_MESSAGES = {
            "processing": ("Commande confirmée", "Votre commande #{id} est en cours de traitement."),
            "shipped":    ("Commande expédiée",  "Votre commande #{id} est en route !"),
            "delivered":  ("Commande livrée",    "Votre commande #{id} a été livrée. Merci !"),
            "canceled":   ("Commande annulée",   "Votre commande #{id} a été annulée."),
        }
        if new_status not in STATUS_MESSAGES:
            return
        order = Order.objects.select_related("author").get(pk=order_id)
        title, body_tpl = STATUS_MESSAGES[new_status]
        token = order.author.fcm_token
        if token:
            send_to_token(
                token=token,
                title=title,
                body=body_tpl.format(id=order.id),
                data={"type": "order_status", "order_id": order.id, "status": new_status},
            )
    except Exception as exc:
        logger.error(f"task_notify_order_status échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def task_notify_proof_submitted(self, order_id):
    try:
        from shop.models.Order import Order
        from notifications.fcm import TOPIC_ADMIN, send_to_topic
        order = Order.objects.select_related("author").get(pk=order_id)
        send_to_topic(
            topic=TOPIC_ADMIN,
            title="Preuve de paiement reçue",
            body=f"Commande #{order.id} — {order.client_name}",
            data={"type": "proof_submitted", "order_id": order.id, "client": order.client_name, "total": order.order_cost_ttc},
        )
    except Exception as exc:
        logger.error(f"task_notify_proof_submitted échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def task_notify_payment_verified(self, order_id):
    try:
        from shop.models.Order import Order
        from notifications.fcm import send_to_token
        order = Order.objects.select_related("author").get(pk=order_id)
        token = order.author.fcm_token
        if token:
            send_to_token(
                token=token,
                title="Paiement confirmé",
                body=f"Votre paiement pour la commande #{order.id} a été vérifié.",
                data={"type": "payment_verified", "order_id": order.id},
            )
    except Exception as exc:
        logger.error(f"task_notify_payment_verified échoué pour commande #{order_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def task_notify_new_customer(self, customer_id):
    try:
        from accounts.models.Customer import Customer
        from notifications.fcm import TOPIC_ADMIN, send_to_topic
        customer = Customer.objects.get(pk=customer_id)
        send_to_topic(
            topic=TOPIC_ADMIN,
            title="Nouveau client inscrit",
            body=f"{customer.get_full_name() or customer.username} — {customer.email}",
            data={"type": "new_customer", "customer_id": str(customer.pk), "email": customer.email},
        )
    except Exception as exc:
        logger.error(f"task_notify_new_customer échoué pour customer #{customer_id} : {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def task_notify_new_product(self, product_id):
    try:
        from shop.models.Product import Product
        from notifications.fcm import TOPIC_MATSTORE, send_to_topic
        product = Product.objects.prefetch_related("images").get(pk=product_id)
        first_image = product.images.first()
        image_url = str(first_image.image) if first_image else ""
        send_to_topic(
            topic=TOPIC_MATSTORE,
            title="Nouveau produit disponible",
            body=f"{product.name} — {product.solde_price} HTG",
            data={"type": "new_product", "product_id": product.id, "product_slug": product.slug, "name": product.name, "price": product.solde_price, "image": image_url},
        )
    except Exception as exc:
        logger.error(f"task_notify_new_product échoué pour produit #{product_id} : {exc}")
        raise self.retry(exc=exc)
