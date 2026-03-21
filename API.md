# MatStore Haiti — API REST

**Base URL** : `https://matstorehaiti.online/api/`
**Auth** : Bearer JWT (`Authorization: Bearer <access_token>`)
**Docs interactives** : `/api/docs/` (Swagger) · `/api/redoc/` (ReDoc)
**Format des erreurs** :
```json
{ "success": false, "error": { "code": "OUT_OF_STOCK", "message": "..." } }
```

---

## Auth — `/api/auth/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/auth/register/` | Public | Inscription + retourne tokens JWT |
| POST | `/auth/login/` | Public | Connexion + retourne tokens JWT |
| POST | `/auth/logout/` | Requis | Blackliste le refresh token |
| POST | `/auth/token/refresh/` | Public | Renouveler l'access token |
| GET | `/auth/me/` | Requis | Profil de l'utilisateur connecté |
| PATCH | `/auth/me/` | Requis | Modifier son profil |
| POST | `/auth/change-password/` | Requis | Changer son mot de passe |
| POST | `/auth/fcm-token/` | Requis | Enregistrer/mettre à jour le FCM token Android |

---

## Produits — `/api/products/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/products/` | Public | Liste paginée avec filtres |
| GET | `/products/search/?q=shea` | Public | Recherche full-text dédiée |
| GET | `/products/{slug}/` | Public | Détail d'un produit |
| GET | `/products/featured/` | Public | Produits mis en avant |
| GET | `/products/new-arrivals/` | Public | Nouveautés (30 derniers jours) |
| GET | `/products/on-sale/` | Public | Produits en promotion |

**Filtres disponibles sur `/products/` :**
```
?category=cosmetiques
?min_price=500&max_price=2000
?in_stock=true
?search=shea
?ordering=solde_price | -solde_price | created_at
```

**Recherche full-text `/products/search/` :**
```
?q=shea butter       → cherche dans nom, description, marque, catégories
```

---

## Catégories — `/api/categories/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/categories/` | Public | Toutes les catégories |
| GET | `/categories/{slug}/` | Public | Détail + produits de la catégorie |

---

## Panier — `/api/cart/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/cart/` | Requis | Voir son panier |
| POST | `/cart/add/` | Requis | Ajouter un produit |
| PATCH | `/cart/update/{item_id}/` | Requis | Modifier la quantité |
| DELETE | `/cart/remove/{item_id}/` | Requis | Supprimer un article |
| DELETE | `/cart/clear/` | Requis | Vider le panier |

---

## Commandes — `/api/orders/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/orders/` | Requis | Historique des commandes |
| POST | `/orders/` | Requis | Passer une commande |
| GET | `/orders/{id}/` | Requis | Détail d'une commande |
| POST | `/orders/{id}/cancel/` | Requis | Annuler (si statut pending) |
| GET | `/orders/{id}/track/?email=x` | **Public** | Suivi commande sans authentification |

**Suivi public** — retourne uniquement : statut, is_paid, transporteur, adresse livraison, total.
Nécessite l'email du client comme vérification : `?email=client@email.com`

**Payload création commande :**
```json
{
  "items": [
    { "product_id": 1, "quantity": 2 }
  ],
  "payment_method": "moncash",
  "delivery_address": {
    "street": "Rue Lamarre",
    "city": "Pétion-Ville",
    "department": "Ouest"
  },
  "notes": "Livrer après 14h"
}
```

**Statuts possibles :** `pending` · `processing` · `shipped` · `delivered` · `canceled`

**Champ `payment_proof`** — présent sur le modèle Order. Visible dans les réponses admin (`/admin/orders/{id}/`). Contient l'URL de la preuve de paiement uploadée pour les commandes hors ligne. `null` pour les autres méthodes.

---

## Paiements — `/api/payments/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/payments/initiate/` | Requis | Initier un paiement |
| POST | `/payments/verify/` | Requis | Vérifier le statut |
| POST | `/payments/webhook/moncash/` | Public | Webhook MonCash |
| POST | `/payments/webhook/stripe/` | Public | Webhook Stripe |

**Méthodes supportées via API :** `moncash` · `natcash` · `stripe`

> **Paiement Hors Ligne** — disponible sur l'interface web (`/checkout/offline-pay/`) mais pas encore exposé comme endpoint REST. Le champ `payment_proof` (image) est stocké sur le modèle `Order`. Pour l'app mobile, voir la section correspondante dans `recommandation_android.md`.

---

## Avis — `/api/reviews/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/reviews/?product={id}` | Public | Avis d'un produit |
| POST | `/reviews/` | Requis + achat vérifié | Laisser un avis |
| PATCH | `/reviews/{id}/` | Propriétaire | Modifier son avis |
| DELETE | `/reviews/{id}/` | Propriétaire | Supprimer son avis |

---

## Favoris — `/api/wishlist/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/wishlist/` | Requis | Liste des favoris |
| POST | `/wishlist/add/` | Requis | Ajouter aux favoris |
| DELETE | `/wishlist/remove/{id}/` | Requis | Retirer des favoris |

---

## Adresses — `/api/addresses/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| GET | `/addresses/` | Requis | Liste des adresses |
| POST | `/addresses/` | Requis | Ajouter une adresse |
| PATCH | `/addresses/{id}/` | Requis | Modifier une adresse |
| DELETE | `/addresses/{id}/` | Requis | Supprimer une adresse |
| PATCH | `/addresses/{id}/default/` | Requis | Définir par défaut |

**Types d'adresse :** `billing` · `shipping`

---

## Back Office Admin — `/api/admin/`

> Tous ces endpoints requièrent `is_staff = True`

### Dashboard
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/dashboard/` | Stats : commandes, revenus, clients, top produits, graphe 30j |

### Produits
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/products/` | Liste complète avec filtres |
| POST | `/admin/products/` | Créer un produit |
| PATCH | `/admin/products/{id}/` | Modifier un produit |
| DELETE | `/admin/products/{id}/` | Supprimer un produit |
| POST | `/admin/products/{id}/images/` | Uploader des images |

### Commandes
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/orders/` | Toutes les commandes + filtres |
| GET | `/admin/orders/{id}/` | Détail complet |
| PATCH | `/admin/orders/{id}/status/` | Changer le statut (déclenche email) |

### Clients
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/customers/` | Liste des clients |
| GET | `/admin/customers/{id}/` | Profil + historique commandes |
| PATCH | `/admin/customers/{id}/` | Modifier un client |

### Catégories
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/categories/` | Liste |
| POST | `/admin/categories/` | Créer |
| PATCH | `/admin/categories/{id}/` | Modifier |
| DELETE | `/admin/categories/{id}/` | Supprimer |

### Inventaire
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/inventory/` | Produits stock faible (`?threshold=10`) |
| PATCH | `/admin/inventory/{id}/` | Mettre à jour le stock |

### Rapports
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/admin/reports/sales/` | Ventes par période (`?period=daily\|weekly\|monthly&start=&end=`) |
| GET | `/admin/reports/products/` | Produits les plus vendus |
| GET | `/admin/reports/customers/` | Meilleurs clients |

---

## Codes d'erreur

| Code | Statut HTTP | Description |
|------|-------------|-------------|
| `OUT_OF_STOCK` | 409 | Produit épuisé |
| `INSUFFICIENT_STOCK` | 409 | Quantité demandée > stock disponible |
| `ORDER_NOT_CANCELLABLE` | 409 | Commande non annulable (déjà traitée) |
| `PAYMENT_FAILED` | 402 | Échec du paiement |
| `INVALID_CREDENTIALS` | 401 | Identifiants incorrects |
| `TOKEN_EXPIRED` | 401 | Token JWT expiré |
| `PERMISSION_DENIED` | 403 | Accès non autorisé |

---

## Tokens JWT

| Token | Durée | Paramètre `.env` |
|-------|-------|-----------------|
| Access | 1 jour | `JWT_ACCESS_TOKEN_LIFETIME_DAYS` |
| Refresh | 30 jours | `JWT_REFRESH_TOKEN_LIFETIME_DAYS` |

Les refresh tokens sont **blacklistés** après rotation.
