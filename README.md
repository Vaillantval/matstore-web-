# MatStore Haiti

**Plateforme e-commerce complète pour la vente de matériaux de construction en Haïti.**

Développée avec Django, Django REST Framework et une application mobile Android (Flutter/Dart),
MatStore Haiti offre une expérience d'achat fluide avec plusieurs méthodes de paiement adaptées
au marché haïtien.

---

## Table des matières

1. [Aperçu du projet](#aperçu-du-projet)
2. [Architecture technique](#architecture-technique)
3. [Fonctionnalités](#fonctionnalités)
4. [Installation locale](#installation-locale)
5. [Variables d'environnement](#variables-denvironnement)
6. [Structure du projet](#structure-du-projet)
7. [API REST](#api-rest)
8. [Systèmes de paiement](#systèmes-de-paiement)
9. [Application mobile Android](#application-mobile-android)
10. [Administration](#administration)
11. [Déploiement Railway](#déploiement-railway)
12. [Auteur](#auteur)

---

## Aperçu du projet

MatStore Haiti est une boutique en ligne spécialisée dans la vente de matériaux de construction, de produits
alimenraires
et de vetements.
Elle s'adresse à la clientèle haïtienne avec des méthodes de paiement locales (MonCash, virement,
dépôt) et internationales (Stripe / carte bancaire).

**Points forts :**

- Catalogue produits avec gestion des stocks et des promotions
- Calcul dynamique des taxes (TVA) et des frais de livraison par transporteur
- Paiement en ligne via Stripe et MonCash
- Paiement hors ligne avec envoi de preuve de paiement
- Application mobile native Android (Flutter)
- Interface d'administration Django enrichie (Jazzmin)
- API REST complète documentée via OpenAPI / Swagger

---

## Architecture technique

| Couche             | Technologie                                            |
|--------------------|--------------------------------------------------------|
| Backend            | Python 3.13 · Django 6.0 · Django REST Framework       |
| Base de données    | PostgreSQL (Railway)                                   |
| Stockage médias    | Volume persistant Railway (`/app/media`)               |
| Paiement en ligne  | Stripe PaymentIntents · MonCash REST API               |
| Notifications      | Resend (API) · Firebase Cloud Messaging (mobile)       |
| Documentation API  | drf-spectacular (OpenAPI 3.0 / Swagger UI)             |
| Application mobile | Flutter 3.x · Dart · Riverpod · Dio · Freezed          |
| Déploiement        | Railway (PaaS) · Gunicorn · WhiteNoise                 |

---

## Fonctionnalités

### Boutique

- Navigation par catégories et filtres
- Recherche produits avec suggestions
- Pages produit avec galerie d'images, description, prix HT/TTC
- Gestion du panier (session ou compte utilisateur)
- Sélection du transporteur avec mise à jour dynamique du récapitulatif

### Tunnel de commande

- Connexion / inscription intégrée au checkout
- Pré-sélection automatique de l'adresse par défaut et du premier transporteur
- Formulaire d'adresse de facturation et de livraison
- Récapitulatif en temps réel (sous-total HT, taxes, livraison, total TTC)
- Plusieurs méthodes de paiement activables depuis l'administration

### Gestion des commandes

- Suivi des statuts : en attente, en cours, expédiée, livrée, annulée
- Historique des commandes dans le tableau de bord client
- Notifications email automatiques (confirmation client, alerte admin)
- Paiement hors ligne avec preuve de paiement jointe

### Compte client

- Inscription, connexion, réinitialisation du mot de passe
- Gestion des adresses multiples avec adresse par défaut
- Tableau de bord personnel (commandes, profil)

---

## Installation locale

### Prérequis

- Python 3.13+
- PostgreSQL 14+
- Node.js (facultatif, pour les outils front)

### Cloner le dépôt

```bash
git clone <URL_DU_DEPOT>
cd matstore
```

### Environnement virtuel

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### Dépendances Python

```bash
pip install -r requirements.txt
```

### Base de données

```bash
# Créer la base de données PostgreSQL
createdb matstore_db

# Appliquer les migrations
python manage.py migrate

# Créer un super-utilisateur
python manage.py createsuperuser
```

### Lancer le serveur de développement

```bash
python manage.py runserver
```

L'application est disponible sur `http://127.0.0.1:8000/`.
La documentation API Swagger est accessible sur `http://127.0.0.1:8000/api/schema/swagger-ui/`.

---

## Variables d'environnement

Créer un fichier `.env` à la racine du projet (ne jamais versionner ce fichier) :

```ini
# -- Django --
SECRET_KEY = votre_cle_secrete_django
DEBUG = False
ALLOWED_HOSTS = votre-domaine.railway.app,localhost

# -- Base de données --
DATABASE_URL = postgresql://user:password@host:5432/matstore_db

# -- Email (Resend) --
RESEND_API_KEY = votre_api_key_resend
DEFAULT_FROM_EMAIL = MatStore Haiti <info@matstorehaiti.online>
ADMINS_NOTIFY = info@matstorehaiti.online
SITE_URL = https://matstorehaiti.online

# -- Stripe --
STRIPE_PUBLIC_KEY = pk_live_...
STRIPE_SECRET_KEY = sk_live_...
STRIPE_WEBHOOK_SECRET = whsec_...

# -- MonCash --
MONCASH_CLIENT_ID = votre_client_id
MONCASH_SECRET_KEY = votre_secret_key
MONCASH_ENVIRONMENT = production   # sandbox | production

# -- Firebase (notifications push mobiles) --
# Coller le contenu JSON complet du fichier téléchargé depuis Firebase Console
# Project Settings → Service Accounts → Generate new private key
FIREBASE_SERVICE_ACCOUNT_JSON = {"type":"service_account",...}
```

---

## Structure du projet

```
matstore/
├── accounts/                   # Authentification et profils clients
│   ├── models/
│   │   └── Customer.py
│   ├── views/
│   └── forms/
│
├── shop/                       # Coeur e-commerce
│   ├── models/
│   │   ├── Product.py
│   │   ├── Category.py
│   │   ├── Order.py
│   │   ├── OrderDetail.py
│   │   ├── Carrier.py
│   │   ├── Method.py
│   │   ├── Setting.py
│   │   └── ExchangeRate.py
│   ├── views/
│   │   ├── checkout_view.py
│   │   ├── payment_view.py
│   │   └── cart_view.py
│   ├── services/
│   │   ├── cart_service.py
│   │   ├── payment_service.py  # Stripe
│   │   └── moncash_service.py
│   └── templatetags/
│       └── price_filters.py
│
├── api/                        # API REST (DRF)
│   ├── auth/
│   ├── products/
│   ├── cart/
│   ├── orders/
│   └── payments/
│
├── dashboard/                  # Espace client (commandes, adresses, profil)
│   ├── models/
│   │   └── Adress.py
│   └── views/
│
├── emails/                     # Utilitaires d'envoi d'emails
│   ├── utils.py
│   ├── signals.py
│   └── apps.py
│
├── templates/                  # Templates HTML Django
│   ├── base.html
│   ├── base_checkout.html
│   ├── shop/
│   │   ├── checkout.html
│   │   ├── cart.html
│   │   ├── payment_success.html
│   │   └── offline_confirm.html
│   └── emails/
│       ├── base_email.html
│       ├── order_confirmation.html
│       ├── order_status_update.html
│       ├── admin_new_order.html
│       └── welcome.html
│
├── static/                     # Fichiers statiques (CSS, JS, images)
├── media/                      # Fichiers uploadés (images produits, preuves de paiement)
├── config/                     # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements.txt
├── Procfile                    # Railway / Gunicorn
├── Dockerfile
├── railway.toml
└── manage.py
```

---

## API REST

L'API est construite avec Django REST Framework et documentée via **drf-spectacular**.

**Documentation interactive :**

- Swagger UI : `GET /api/schema/swagger-ui/`
- ReDoc : `GET /api/schema/redoc/`
- Schéma OpenAPI JSON : `GET /api/schema/`

### Authentification

| Méthode   | Endpoint                   | Description                                      |
|-----------|----------------------------|--------------------------------------------------|
| POST      | `/api/auth/login/`         | Connexion (retourne access + refresh JWT)        |
| POST      | `/api/auth/register/`      | Inscription                                      |
| POST      | `/api/auth/token/refresh/` | Renouvellement du token d'accès                  |
| POST      | `/api/auth/logout/`        | Déconnexion (blacklist du refresh token)         |
| GET/PATCH | `/api/auth/profile/`       | Profil de l'utilisateur connecté                 |
| POST      | `/api/auth/fcm-token/`     | Enregistrement du token FCM (notifications push) |

> **Note :** Le token FCM est géré séparément via `POST /api/auth/fcm-token/` après le login.
> Ne pas inclure `fcm_token` dans le payload de `POST /api/auth/login/`.

**Tokens JWT :**

- Access token : durée de vie **1 jour**
- Refresh token : durée de vie **30 jours**

```
Authorization: Bearer <access_token>
```

### Catalogue

| Méthode | Endpoint                         | Description                                         |
|---------|----------------------------------|-----------------------------------------------------|
| GET     | `/api/products/`                 | Liste des produits (filtres, recherche, pagination) |
| GET     | `/api/products/{id}/`            | Détail d'un produit                                 |
| GET     | `/api/categories/`               | Liste des catégories                                |
| GET     | `/api/categories/{id}/products/` | Produits par catégorie                              |

### Panier et Commandes

| Méthode | Endpoint            | Description                            |
|---------|---------------------|----------------------------------------|
| GET     | `/api/cart/`        | Contenu du panier                      |
| POST    | `/api/cart/add/`    | Ajouter un article                     |
| PATCH   | `/api/cart/update/` | Modifier la quantité                   |
| DELETE  | `/api/cart/remove/` | Retirer un article                     |
| GET     | `/api/orders/`      | Historique des commandes (auth requis) |
| GET     | `/api/orders/{id}/` | Détail d'une commande                  |
| POST    | `/api/orders/`      | Créer une commande                     |

### Paiement

| Méthode | Endpoint                  | Description                                 |
|---------|---------------------------|---------------------------------------------|
| GET     | `/api/carriers/`          | Liste des transporteurs avec tarifs         |
| GET     | `/api/payment-methods/`   | Méthodes de paiement disponibles            |
| POST    | `/api/payments/initiate/` | Initier un paiement (Stripe / MonCash)      |
| POST    | `/api/payments/verify/`   | Vérifier le statut d'un paiement            |
| POST    | `/api/payments/offline/`  | Soumettre une preuve de paiement hors ligne |

### Adresses

| Méthode | Endpoint                           | Description                      |
|---------|------------------------------------|----------------------------------|
| GET     | `/api/addresses/`                  | Adresses de l'utilisateur        |
| POST    | `/api/addresses/`                  | Ajouter une adresse              |
| PATCH   | `/api/addresses/{id}/`             | Modifier une adresse             |
| DELETE  | `/api/addresses/{id}/`             | Supprimer une adresse            |
| PATCH   | `/api/addresses/{id}/set-default/` | Définir comme adresse par défaut |

---

## Systèmes de paiement

### Stripe

Paiement par carte bancaire internationale via **Stripe PaymentIntents**.

- Les montants sont facturés en **USD**
- Conversion automatique depuis la devise de base configurée dans les paramètres du site
- Confirmation de paiement côté client via Stripe.js (Elements)
- Callback de succès : `GET /payment/success/?payment_intent=pi_xxx`

### MonCash

Paiement mobile local via **MonCash** (Digicel Haiti).

- Seule la devise **HTG (Gourdes haïtiennes)** est acceptée par MonCash
- Conversion automatique depuis la devise de base si nécessaire (taux dans `ExchangeRate`)
- Identifiant de commande unique envoyé à MonCash : `{order_id}-{uuid8}`
- Callback de retour : `GET /payment/moncash/callback/?transactionId=xxx`
- Vérification du montant payé avec tolérance de 1 HTG

### Paiement hors ligne

Pour les clients souhaitant payer par virement bancaire, dépôt ou autre.

**Flux API (application mobile) :**

1. Le client crée la commande avec `payment_method="offline"` via `POST /api/orders/`
2. Le client effectue le virement ou le dépôt physiquement
3. Le client uploade la preuve (JPG/PNG, max 5 MB) via `POST /api/payments/offline/`
4. L'admin reçoit un email de notification automatique
5. L'admin vérifie la preuve et met à jour le statut de paiement dans l'interface Django
6. Le client suit l'état via `payment_status` : `unpaid` → `proof_submitted` → `verified` → `paid`

**Règles :**

- La commande doit avoir `payment_method="offline"` pour accepter la preuve
- Formats acceptés : JPG, PNG — taille maximale : 5 MB
- La commande reste `is_paid=False` jusqu'à validation manuelle de l'admin
- Notifications email automatiques envoyées au client et à l'administrateur

---

## Application mobile Android

L'application mobile est développée en **Flutter / Dart** et cible Android.

### Stack technique

```yaml
dependencies:
  flutter_riverpod: ^2.6.1         # Gestion d'état
  dio: ^5.7.0                      # Client HTTP
  flutter_secure_storage: ^9.2.2   # Stockage sécurisé des tokens JWT
  cached_network_image: ^3.4.1     # Cache images réseau
  firebase_messaging: ^15.1.4      # Notifications push (FCM)
  freezed_annotation: ^2.4.4       # Modèles immutables
  json_annotation: ^4.9.0          # Sérialisation JSON
  fl_chart: ^0.69.0                # Graphiques (dashboard admin)

dev_dependencies:
  build_runner: ^2.4.13
  freezed: ^2.5.7
  json_serializable: ^6.8.0
```

### Modèles Dart avec Freezed

```dart
@freezed
class Product with _$Product {
  const factory Product({
    required int id,
    required String name,
    required String description,
    required double regularPrice,
    double? soldePrice,
    required String imageUrl,
    required int stock,
  }) = _Product;

  factory Product.fromJson(Map<String, dynamic> json) =>
      _$ProductFromJson(json);
}
```

Générer les fichiers de sérialisation :

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### Architecture Flutter

```
lib/
├── core/
│   ├── api/            # Client Dio + intercepteurs JWT (auto-refresh)
│   ├── models/         # Modèles Freezed + json_serializable
│   └── providers/      # Riverpod providers globaux
└── features/
    ├── auth/           # Login, Register, Profile
    ├── catalog/        # ProductList, ProductDetail, CategoryList
    ├── cart/           # Cart, Checkout
    ├── orders/         # OrderList, OrderDetail
    └── dashboard/      # DashboardHome, AddressList
```

### Notifications push (FCM)

1. L'application obtient un token FCM au démarrage via `FirebaseMessaging.instance.getToken()`
2. Après login réussi, envoyer le token via `POST /api/auth/fcm-token/`
3. Le backend utilise ce token pour envoyer des notifications ciblées (confirmation de commande, changement de statut de
   livraison)

---

## Administration

L'interface d'administration Django (`/admin/`) permet de gérer l'ensemble de la plateforme.

### Modules disponibles

| Module                   | Fonctionnalités                                                       |
|--------------------------|-----------------------------------------------------------------------|
| **Produits**             | Création, modification, images, gestion du stock, prix promo          |
| **Catégories**           | Arborescence, images de catégorie                                     |
| **Commandes**            | Suivi des statuts, détail des articles, preuve de paiement hors ligne |
| **Clients**              | Liste, profil, historique des commandes                               |
| **Transporteurs**        | Nom, tarif, activation/désactivation                                  |
| **Méthodes de paiement** | Activation par méthode (Stripe, MonCash, Hors Ligne)                  |
| **Paramètres**           | Devise de base, taux de TVA, coordonnées de la boutique, APK Android  |
| **Taux de change**       | Gestion des paires de devises (HTG, USD, EUR...)                      |

### Gestion des taux de change

Les taux de change sont stockés en base de données et peuvent être actualisés depuis l'interface
d'administration dans la section **Settings > Actualiser les taux**.

---

## Déploiement Railway

Le projet est déployé sur **Railway** (PaaS) avec les services suivants :

- Service Web (Django + Gunicorn)
- Service PostgreSQL (base de données managée)
- Volume persistant pour les fichiers médias (`/app/media`)

### Fichiers de déploiement

**`Dockerfile`** — build de l'image avec collectstatic intégré.

**`railway.toml`** — commande de démarrage :

```bash
python manage.py migrate --noinput && python init_site.py && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 4 --worker-class gthread --timeout 120
```

**`requirements.txt`** inclut `gunicorn`, `psycopg2-binary`, `whitenoise`, `dj-database-url`.

### Variables Railway à configurer

Toutes les variables listées dans la section [Variables d'environnement](#variables-denvironnement)
doivent être définies dans le panneau Railway > Service > Variables.

### Volume persistant

Le volume Railway est monté sur `/app/media`. Les fichiers uploadés (logos, images produits,
preuves de paiement, APK Android) sont persistés entre les déploiements.

---

## Auteur

**Valcin Vaillant**
Développeur & Ingénieur — Faculté des Sciences (FDS-UEH)
*Université d'État d'Haïti*

Conception, développement et déploiement complets de la plateforme MatStore Haiti :
backend Django, API REST, intégrations de paiement (Stripe, MonCash), application mobile Flutter,
et infrastructure Railway.

---

*MatStore Haiti — Votre partenaire de confiance pour les matériaux de construction.*
