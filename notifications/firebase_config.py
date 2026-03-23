import json
import logging
import os

import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)


def initialize_firebase():
    """Initialise le SDK Firebase Admin depuis la variable d'environnement Railway."""
    if firebase_admin._apps:
        return  # Déjà initialisé

    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        logger.warning(
            "FIREBASE_SERVICE_ACCOUNT_JSON non défini — "
            "les notifications push FCM sont désactivées."
        )
        return

    try:
        service_account_info = json.loads(raw)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialisé.")
    except Exception as e:
        logger.error(f"Erreur initialisation Firebase : {e}")
