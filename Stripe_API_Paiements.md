# Stripe API — Paiements (PaymentIntents & Charges)

> Documentation de référence pour l'intégration des paiements Stripe dans KouLakay.  
> Version API : **2024-06-20** • Langue : Python (Django)

---

## Table des matières

- [Authentification](#authentification)
- [Environnements](#environnements)
- [PaymentIntents](#paymentintents)
  - [Créer un PaymentIntent](#créer-un-paymentintent)
  - [Confirmer un PaymentIntent](#confirmer-un-paymentintent)
  - [Récupérer un PaymentIntent](#récupérer-un-paymentintent)
  - [Annuler un PaymentIntent](#annuler-un-paymentintent)
  - [Lister les PaymentIntents](#lister-les-paymentintents)
- [Charges](#charges)
  - [Créer une Charge](#créer-une-charge)
  - [Récupérer une Charge](#récupérer-une-charge)
  - [Lister les Charges](#lister-les-charges)
- [Cycle de vie d'un paiement](#cycle-de-vie-dun-paiement)
- [Statuts des PaymentIntents](#statuts-des-paymentintents)
- [Gestion des erreurs](#gestion-des-erreurs)
- [Webhooks Stripe](#webhooks-stripe)
  - [Événements importants](#événements-importants)
  - [Vérification de signature](#vérification-de-signature)
  - [Exemple de webhook Django](#exemple-de-webhook-django)
- [Intégration Django complète](#intégration-django-complète)
- [Codes d'erreur courants](#codes-derreur-courants)
- [Clés de test](#clés-de-test)

---

## Authentification

Toutes les requêtes Stripe doivent inclure ta clé secrète dans le header `Authorization`.

```bash
# Format HTTP
Authorization: Bearer sk_live_XXXXXXXXXXXXXXXXXXXX

# Avec curl
curl https://api.stripe.com/v1/payment_intents \
  -u sk_live_XXXXXXXXXXXXXXXXXXXX:
```

```python
# Installation
pip install stripe

# Configuration Django (settings.py)
import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
```

> ⚠️ Ne jamais exposer la clé secrète côté frontend. Utilise uniquement la clé **publiable** (`pk_...`) dans le JavaScript.

---

## Environnements

| Mode | Clé secrète | Clé publiable | URL de base |
|---|---|---|---|
| **Test** | `sk_test_...` | `pk_test_...` | `https://api.stripe.com` |
| **Live** | `sk_live_...` | `pk_live_...` | `https://api.stripe.com` |

```python
# .env
STRIPE_SECRET_KEY=sk_live_...       # ou sk_test_... pour les tests
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## PaymentIntents

Le `PaymentIntent` est l'objet central de l'API Stripe moderne. Il représente l'intention de collecter un paiement et suit son cycle de vie complet.

### Créer un PaymentIntent

**`POST /v1/payment_intents`**

```bash
curl -X POST https://api.stripe.com/v1/payment_intents \
  -u sk_test_...: \
  -d amount=2000 \
  -d currency=usd \
  -d "payment_method_types[]"=card \
  -d "metadata[order_id]"=koulakay_cours_001
```

```python
import stripe

payment_intent = stripe.PaymentIntent.create(
    amount=2000,                    # En centimes : 2000 = 20.00 USD
    currency="usd",
    payment_method_types=["card"],
    metadata={
        "order_id": "koulakay_cours_001",
        "user_id": "42",
        "cours": "Django Avancé",
    },
    description="Inscription cours Django Avancé — KouLakay",
    receipt_email="etudiant@example.com",
)

print(payment_intent.client_secret)  # À envoyer au frontend
```

**Paramètres principaux**

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `amount` | integer | ✅ | Montant en centimes (USD) ou unité de base |
| `currency` | string | ✅ | Code ISO 4217 (`usd`, `eur`, `htg`...) |
| `payment_method_types` | array | ✅ | Ex: `["card"]` |
| `description` | string | ❌ | Visible dans le dashboard Stripe |
| `receipt_email` | string | ❌ | Email pour l'envoi du reçu |
| `metadata` | object | ❌ | Données custom (order_id, user_id...) |
| `customer` | string | ❌ | ID d'un objet Customer Stripe |
| `confirm` | boolean | ❌ | Confirmer immédiatement si `true` |

**Réponse**

```json
{
  "id": "pi_3OaBcDeFgHiJkLmN1234567",
  "object": "payment_intent",
  "amount": 2000,
  "amount_received": 0,
  "currency": "usd",
  "status": "requires_payment_method",
  "client_secret": "pi_3OaBcDeFgHiJkLmN1234567_secret_AbCdEfGhIjKlMnOpQr",
  "created": 1710000000,
  "description": "Inscription cours Django Avancé — KouLakay",
  "metadata": {
    "order_id": "koulakay_cours_001",
    "user_id": "42"
  },
  "payment_method_types": ["card"],
  "livemode": false
}
```

---

### Confirmer un PaymentIntent

**`POST /v1/payment_intents/:id/confirm`**

```bash
curl -X POST https://api.stripe.com/v1/payment_intents/pi_xxx/confirm \
  -u sk_test_...: \
  -d payment_method=pm_card_visa
```

```python
payment_intent = stripe.PaymentIntent.confirm(
    "pi_3OaBcDeFgHiJkLmN1234567",
    payment_method="pm_card_visa",
    return_url="https://koulakay.ht/paiement/retour/",
)
```

> ℹ️ En pratique avec Stripe.js, la confirmation se fait côté frontend avec `stripe.confirmCardPayment(clientSecret)`.

---

### Récupérer un PaymentIntent

**`GET /v1/payment_intents/:id`**

```bash
curl https://api.stripe.com/v1/payment_intents/pi_3OaBcDeFgHiJkLmN1234567 \
  -u sk_test_...:
```

```python
payment_intent = stripe.PaymentIntent.retrieve(
    "pi_3OaBcDeFgHiJkLmN1234567"
)

print(payment_intent.status)        # "succeeded"
print(payment_intent.amount)        # 2000
print(payment_intent.amount_received)  # 2000
```

---

### Annuler un PaymentIntent

**`POST /v1/payment_intents/:id/cancel`**

Possible uniquement si le statut est `requires_payment_method`, `requires_capture`, `requires_confirmation`, ou `requires_action`.

```bash
curl -X POST https://api.stripe.com/v1/payment_intents/pi_xxx/cancel \
  -u sk_test_...:
```

```python
payment_intent = stripe.PaymentIntent.cancel(
    "pi_3OaBcDeFgHiJkLmN1234567",
    cancellation_reason="requested_by_customer",  # optionnel
)
```

**Raisons d'annulation acceptées**

| Valeur | Description |
|---|---|
| `duplicate` | Doublon de transaction |
| `fraudulent` | Transaction frauduleuse suspectée |
| `requested_by_customer` | Annulation à la demande du client |
| `abandoned` | Paiement abandonné |

---

### Lister les PaymentIntents

**`GET /v1/payment_intents`**

```bash
curl "https://api.stripe.com/v1/payment_intents?limit=10" \
  -u sk_test_...:
```

```python
payment_intents = stripe.PaymentIntent.list(
    limit=20,
    created={"gte": 1710000000},    # Depuis une date (timestamp Unix)
)

for pi in payment_intents.auto_paging_iter():
    print(pi.id, pi.status, pi.amount)
```

**Paramètres de filtrage**

| Paramètre | Description |
|---|---|
| `limit` | Nombre de résultats (1–100, défaut: 10) |
| `starting_after` | Curseur de pagination (ID du dernier objet) |
| `ending_before` | Curseur de pagination inverse |
| `created[gte]` | Filtre date (timestamp Unix) |
| `customer` | Filtrer par ID client |

---

## Charges

> ⚠️ **Attention** : L'objet `Charge` est l'ancienne API. Pour les nouveaux projets, utilise **PaymentIntents**. Les `Charge` sont toutefois encore utilisées pour vérifier le résultat d'un paiement.

### Créer une Charge

**`POST /v1/charges`**

```bash
curl -X POST https://api.stripe.com/v1/charges \
  -u sk_test_...: \
  -d amount=2000 \
  -d currency=usd \
  -d source=tok_visa \
  -d description="Cours KouLakay"
```

```python
charge = stripe.Charge.create(
    amount=2000,
    currency="usd",
    source="tok_visa",              # Token de carte (généré par Stripe.js)
    description="Cours KouLakay",
    metadata={"order_id": "001"},
)
```

**Réponse**

```json
{
  "id": "ch_3OaBcDeFgHiJkLmN1234567",
  "object": "charge",
  "amount": 2000,
  "amount_captured": 2000,
  "captured": true,
  "currency": "usd",
  "description": "Cours KouLakay",
  "paid": true,
  "status": "succeeded",
  "payment_intent": "pi_3OaBcDeFgHiJkLmN1234567",
  "receipt_url": "https://pay.stripe.com/receipts/...",
  "created": 1710000000
}
```

---

### Récupérer une Charge

**`GET /v1/charges/:id`**

```python
charge = stripe.Charge.retrieve("ch_3OaBcDeFgHiJkLmN1234567")
print(charge.status)     # "succeeded"
print(charge.paid)       # True
```

---

### Lister les Charges

**`GET /v1/charges`**

```python
charges = stripe.Charge.list(limit=10)

for charge in charges.auto_paging_iter():
    print(charge.id, charge.amount, charge.status)
```

---

## Cycle de vie d'un paiement

```
Création du PaymentIntent
         │
         ▼
requires_payment_method  ──► (méthode de paiement ajoutée)
         │
         ▼
requires_confirmation     ──► (confirmation déclenchée)
         │
         ▼
requires_action           ──► (3D Secure / authentification)
         │
         ▼
processing                ──► (traitement en cours)
         │
    ┌────┴────┐
    ▼         ▼
succeeded   requires_capture ──► (capture manuelle)
    │              │
    │              ▼
    │          succeeded
    │
    ▼
 canceled   (annulable depuis la plupart des étapes)
```

---

## Statuts des PaymentIntents

| Statut | Description |
|---|---|
| `requires_payment_method` | En attente d'une méthode de paiement |
| `requires_confirmation` | En attente de confirmation |
| `requires_action` | Authentification 3D Secure requise |
| `processing` | Traitement en cours |
| `requires_capture` | En attente de capture manuelle |
| `succeeded` | Paiement réussi ✅ |
| `canceled` | Annulé ❌ |

---

## Gestion des erreurs

Stripe retourne des erreurs structurées. Voici comment les intercepter en Python :

```python
import stripe
from stripe.error import (
    CardError,
    InvalidRequestError,
    AuthenticationError,
    APIConnectionError,
    StripeError,
)

try:
    payment_intent = stripe.PaymentIntent.create(
        amount=2000,
        currency="usd",
        payment_method_types=["card"],
    )

except CardError as e:
    # Carte refusée
    err = e.error
    print(f"Carte refusée : {err.code}")
    print(f"Message : {err.message}")
    print(f"Param : {err.param}")
    # Codes courants : card_declined, insufficient_funds, expired_card

except InvalidRequestError as e:
    # Paramètre invalide (ex: amount négatif)
    print(f"Requête invalide : {e.user_message}")

except AuthenticationError as e:
    # Clé API incorrecte
    print("Clé API invalide")

except APIConnectionError as e:
    # Problème réseau
    print("Impossible de joindre Stripe")

except StripeError as e:
    # Erreur Stripe générique
    print(f"Erreur Stripe : {e.user_message}")
```

**Structure d'une erreur**

```json
{
  "error": {
    "type": "card_error",
    "code": "card_declined",
    "decline_code": "insufficient_funds",
    "message": "Your card has insufficient funds.",
    "param": "payment_method",
    "doc_url": "https://stripe.com/docs/error-codes/card-declined"
  }
}
```

---

## Webhooks Stripe

Les webhooks permettent à Stripe de notifier ton backend lorsqu'un événement se produit (paiement réussi, échoué, remboursé...).

### Événements importants

| Événement | Description |
|---|---|
| `payment_intent.succeeded` | Paiement réussi ✅ → débloquer l'accès au cours |
| `payment_intent.payment_failed` | Paiement échoué ❌ |
| `payment_intent.canceled` | Paiement annulé |
| `payment_intent.created` | Nouveau PaymentIntent créé |
| `charge.succeeded` | Charge réussie |
| `charge.refunded` | Remboursement effectué |
| `charge.dispute.created` | Litige ouvert par le client |

---

### Vérification de signature

Toujours vérifier la signature Stripe pour sécuriser le endpoint webhook.

```python
import stripe
from django.conf import settings

webhook_secret = settings.STRIPE_WEBHOOK_SECRET

payload = request.body
sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

try:
    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )
except ValueError:
    # Payload invalide
    return HttpResponse(status=400)
except stripe.error.SignatureVerificationError:
    # Signature invalide
    return HttpResponse(status=400)
```

---

### Exemple de webhook Django

```python
# views.py
import stripe
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Order, Enrollment

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    # 1. Vérifier la signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    # 2. Traiter l'événement
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        handle_payment_succeeded(data)

    elif event_type == "payment_intent.payment_failed":
        handle_payment_failed(data)

    elif event_type == "charge.refunded":
        handle_refund(data)

    # 3. Toujours retourner 200 à Stripe
    return HttpResponse(status=200)


def handle_payment_succeeded(payment_intent):
    """Débloquer l'accès au cours après paiement réussi."""
    order_id = payment_intent["metadata"].get("order_id")
    user_id  = payment_intent["metadata"].get("user_id")

    if not order_id or not user_id:
        return

    try:
        order = Order.objects.get(id=order_id)
        order.status = "paid"
        order.stripe_payment_intent = payment_intent["id"]
        order.save()

        # Créer l'inscription Thinkific
        Enrollment.objects.get_or_create(
            user_id=user_id,
            course_id=order.course_id,
        )

    except Order.DoesNotExist:
        pass


def handle_payment_failed(payment_intent):
    """Marquer la commande comme échouée."""
    order_id = payment_intent["metadata"].get("order_id")
    if order_id:
        Order.objects.filter(id=order_id).update(status="failed")


def handle_refund(charge):
    """Traiter un remboursement."""
    payment_intent_id = charge.get("payment_intent")
    Order.objects.filter(
        stripe_payment_intent=payment_intent_id
    ).update(status="refunded")
```

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("api/webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
```

---

## Intégration Django complète

Voici le flux complet pour un paiement de cours sur KouLakay :

```python
# views.py — Créer un PaymentIntent côté backend
import stripe
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_POST
def create_payment_intent(request):
    data = json.loads(request.body)
    course_id = data.get("course_id")

    try:
        course = Course.objects.get(id=course_id)

        intent = stripe.PaymentIntent.create(
            amount=int(course.price_usd * 100),   # Convertir en centimes
            currency="usd",
            payment_method_types=["card"],
            metadata={
                "order_id": str(order.id),
                "user_id": str(request.user.id),
                "course_id": str(course_id),
            },
            description=f"KouLakay — {course.title}",
            receipt_email=request.user.email,
        )

        return JsonResponse({
            "clientSecret": intent.client_secret,
            "paymentIntentId": intent.id,
        })

    except Course.DoesNotExist:
        return JsonResponse({"error": "Cours introuvable"}, status=404)
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e.user_message)}, status=400)
```

```javascript
// Frontend — Confirmer le paiement avec Stripe.js
const stripe = Stripe("pk_live_...");

const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
  payment_method: {
    card: cardElement,
    billing_details: { name: "Nom du client" },
  },
});

if (error) {
  console.error("Paiement échoué :", error.message);
} else if (paymentIntent.status === "succeeded") {
  console.log("Paiement réussi !");
  // Rediriger vers la page de confirmation
}
```

---

## Codes d'erreur courants

| Code | Description | Action recommandée |
|---|---|---|
| `card_declined` | Carte refusée | Demander une autre carte |
| `insufficient_funds` | Solde insuffisant | Informer le client |
| `expired_card` | Carte expirée | Mettre à jour la carte |
| `incorrect_cvc` | CVC incorrect | Vérifier le code |
| `incorrect_number` | Numéro de carte invalide | Vérifier le numéro |
| `processing_error` | Erreur de traitement | Réessayer plus tard |
| `rate_limit` | Trop de requêtes | Implémenter un backoff |
| `authentication_required` | 3DS requis | Déclencher l'authentification |

---

## Clés de test

Stripe fournit des cartes de test pour simuler différents scénarios :

| Numéro de carte | Résultat |
|---|---|
| `4242 4242 4242 4242` | Succès ✅ |
| `4000 0000 0000 0002` | Carte refusée ❌ |
| `4000 0000 0000 9995` | Fonds insuffisants ❌ |
| `4000 0025 0000 3155` | Authentification 3DS requise |
| `4000 0000 0000 0069` | Carte expirée ❌ |
| `4000 0000 0000 0127` | CVC incorrect ❌ |

> Pour toutes les cartes de test : date d'expiration `12/34`, CVC `123`, code postal `12345`.

---

## Références

- Documentation officielle : https://stripe.com/docs/api
- Guide PaymentIntents : https://stripe.com/docs/payments/payment-intents
- Dashboard Stripe : https://dashboard.stripe.com
- Stripe CLI (tests webhooks en local) : https://stripe.com/docs/stripe-cli

---

> Document préparé par Transversal • Port-au-Prince, Haïti • 2026
