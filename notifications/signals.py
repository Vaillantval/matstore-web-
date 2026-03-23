import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.fcm import (
    TOPIC_ADMIN,
    TOPIC_MATSTORE,
    send_to_token,
    send_to_topic,
)
from shop.models.Order import Order
from shop.models.Product import Product

logger = logging.getLogger(__name__)


# ── 1. Nouvelle commande ──────────────────────────────────────────────────────
@receiver(post_save, sender=Order)
def notify_new_order(sender, instance, created, **kwargs):
    if not created:
        return

    # Notification au client (token ciblé)
    token = instance.author.fcm_token
    if token:
        send_to_token(
            token=token,
            title="Commande recue",
            body=f"Votre commande #{instance.id} a bien ete enregistree.",
            data={
                "type": "new_order",
                "order_id": instance.id,
                "total": instance.order_cost_ttc,
                "status": instance.status,
            },
        )

    # Notification aux admins (topic)
    send_to_topic(
        topic=TOPIC_ADMIN,
        title=f"Nouvelle commande #{instance.id}",
        body=f"{instance.client_name} — {instance.order_cost_ttc} HTG",
        data={
            "type": "new_order_admin",
            "order_id": instance.id,
            "client_name": instance.client_name,
            "total": instance.order_cost_ttc,
            "payment_method": instance.payment_method,
        },
    )


# ── 2. Changement de statut commande → client ─────────────────────────────────
# Pas de pre_save ici : emails/signals.py capture déjà _old_status sur l'instance.

STATUS_MESSAGES = {
    "processing": ("Commande confirmee", "Votre commande #{id} est en cours de traitement."),
    "shipped":    ("Commande expediee",  "Votre commande #{id} est en route !"),
    "delivered":  ("Commande livree",    "Votre commande #{id} a ete livree. Merci !"),
    "canceled":   ("Commande annulee",   "Votre commande #{id} a ete annulee."),
}


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    if old_status is None or old_status == instance.status:
        return
    if instance.status not in STATUS_MESSAGES:
        return

    title, body_tpl = STATUS_MESSAGES[instance.status]
    body = body_tpl.format(id=instance.id)

    token = instance.author.fcm_token
    if token:
        send_to_token(
            token=token,
            title=title,
            body=body,
            data={
                "type": "order_status",
                "order_id": instance.id,
                "status": instance.status,
            },
        )


# ── 3. Preuve de paiement soumise → admins ────────────────────────────────────
# Pas de pre_save ici : emails/signals.py capture déjà _old_payment_status.

@receiver(post_save, sender=Order)
def notify_proof_submitted(sender, instance, created, **kwargs):
    if created:
        return

    old_payment = getattr(instance, "_old_payment_status", None)
    if old_payment != "unpaid" or instance.payment_status != "proof_submitted":
        return

    send_to_topic(
        topic=TOPIC_ADMIN,
        title="Preuve de paiement recue",
        body=f"Commande #{instance.id} — {instance.client_name}",
        data={
            "type": "proof_submitted",
            "order_id": instance.id,
            "client": instance.client_name,
            "total": instance.order_cost_ttc,
        },
    )


# ── 4. Paiement offline confirmé (verified) → client ─────────────────────────

@receiver(post_save, sender=Order)
def notify_payment_verified(sender, instance, created, **kwargs):
    if created:
        return

    old_payment = getattr(instance, "_old_payment_status", None)
    if old_payment != "proof_submitted" or instance.payment_status != "verified":
        return

    token = instance.author.fcm_token
    if token:
        send_to_token(
            token=token,
            title="Paiement confirme",
            body=f"Votre paiement pour la commande #{instance.id} a ete verifie.",
            data={
                "type": "payment_verified",
                "order_id": instance.id,
            },
        )


# ── 5. Nouveau produit disponible → tous les utilisateurs ────────────────────

@receiver(post_save, sender=Product)
def notify_new_product(sender, instance, created, **kwargs):
    if not created or not instance.is_available:
        return

    first_image = instance.images.first()
    image_url = str(first_image.image) if first_image else ""

    send_to_topic(
        topic=TOPIC_MATSTORE,
        title="Nouveau produit disponible",
        body=f"{instance.name} — {instance.solde_price} HTG",
        data={
            "type": "new_product",
            "product_id": instance.id,
            "product_slug": instance.slug,
            "name": instance.name,
            "price": instance.solde_price,
            "image": image_url,
        },
    )
