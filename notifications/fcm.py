import logging

import firebase_admin
from firebase_admin import messaging

logger = logging.getLogger(__name__)

TOPIC_MATSTORE = "matstore"  # tous les utilisateurs connectés
TOPIC_ADMIN = "admin"        # administrateurs seulement


def _is_ready():
    """Vérifie que Firebase est initialisé avant tout envoi."""
    return bool(firebase_admin._apps)


def send_to_token(token: str, title: str, body: str, data: dict = None):
    """Envoie une notification push à un appareil ciblé via son FCM token."""
    if not _is_ready() or not token:
        return False
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="ic_notification",
                    color="#ff5722",
                    sound="default",
                ),
            ),
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"FCM token envoyé : {response}")
        return True
    except Exception as e:
        logger.error(f"FCM send_to_token erreur : {e}")
        return False


def send_to_topic(topic: str, title: str, body: str, data: dict = None):
    """Envoie une notification push à tous les abonnés d'un topic."""
    if not _is_ready():
        return False
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="ic_notification",
                    color="#ff5722",
                    sound="default",
                ),
            ),
            topic=topic,
        )
        response = messaging.send(message)
        logger.info(f"FCM topic '{topic}' envoyé : {response}")
        return True
    except Exception as e:
        logger.error(f"FCM send_to_topic erreur : {e}")
        return False


def subscribe_to_topic(token: str, topic: str):
    """Abonne un FCM token à un topic."""
    if not _is_ready() or not token:
        return False
    try:
        response = messaging.subscribe_to_topic([token], topic)
        if response.failure_count > 0:
            logger.warning(f"Echec abonnement topic '{topic}' : {response.errors}")
        return response.success_count > 0
    except Exception as e:
        logger.error(f"FCM subscribe_to_topic erreur : {e}")
        return False


def unsubscribe_from_topic(token: str, topic: str):
    """Désabonne un FCM token d'un topic."""
    if not _is_ready() or not token:
        return False
    try:
        messaging.unsubscribe_from_topic([token], topic)
        return True
    except Exception as e:
        logger.error(f"FCM unsubscribe_from_topic erreur : {e}")
        return False
