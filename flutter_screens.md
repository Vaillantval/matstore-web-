# Flutter Android — Écrans & Modèles — MatStore Haiti

> Complément de `API.md` (endpoints) et `recommandation_android.md` (packages, patterns).
> Ce fichier décrit **chaque écran** (route, données, UI, navigation) et les **modèles Dart** exacts issus des serializers API.

---

## Sommaire

1. [Modèles Dart](#1-modèles-dart)
2. [Navigation — carte des routes](#2-navigation--carte-des-routes)
3. [Écrans Auth](#3-écrans-auth)
4. [Écrans principaux (bottom nav)](#4-écrans-principaux-bottom-nav)
5. [Écrans Produits](#5-écrans-produits)
6. [Flux Checkout](#6-flux-checkout)
7. [Écrans Commandes](#7-écrans-commandes)
8. [Écrans Compte](#8-écrans-compte)
9. [Écrans Annexes](#9-écrans-annexes)
10. [Providers Riverpod suggérés](#10-providers-riverpod-suggérés)

---

## 1. Modèles Dart

> Chaque modèle correspond exactement aux champs retournés par l'API.
> Utiliser `freezed` + `json_serializable` pour la génération du code.

### 1.1 Auth

```dart
// POST /auth/login/ ou /auth/register/ → tokens dans la réponse
class AuthTokens {
  final String access;
  final String refresh;
}

// GET/PATCH /auth/me/
class UserProfile {
  final int     id;
  final String  username;
  final String  email;
  final String  firstName;
  final String  lastName;
  final bool    isStaff;
  final String? phone;
  final String? fcmToken;
  final DateTime dateJoined;
}
```

### 1.2 Produits

```dart
// Utilisé dans les listes et le panier
class ProductImage {
  final int    id;
  final String image;   // URL absolue Railway
}

class CategoryBrief {
  final int    id;
  final String name;
  final String slug;
}

// GET /products/ — liste
class Product {
  final int           id;
  final String        name;
  final String        slug;
  final String        description;
  final double        price;          // solde_price (prix de vente)
  final double        compareAtPrice; // regular_price (prix barré)
  final String        currency;       // ex: "HTG"
  final List<ProductImage> images;
  final CategoryBrief?     category;  // première catégorie
  final bool          inStock;
  final int           stockQuantity;
  final double?       ratingAverage;  // null si aucun avis
  final int           ratingCount;
  final DateTime      createdAt;
}

// GET /products/{slug}/ — détail (hérite de Product +)
class ProductDetail extends Product {
  final String?           moreDescription;
  final String?           additionalInfo;
  final String?           brand;
  final bool              isBestSeller;
  final bool              isFeatured;
  final bool              isNewArrival;
  final bool              isSpecialOffer;
  final List<CategoryBrief> categories;   // toutes les catégories
  final DateTime          updatedAt;
}
```

### 1.3 Catégories

```dart
// GET /categories/
class Category {
  final int    id;
  final String name;
  final String slug;
  final String? image;   // URL
}

// GET /categories/{slug}/ — inclut les produits
class CategoryDetail extends Category {
  final List<Product> products;
}
```

### 1.4 Panier

```dart
class CartItem {
  final int      id;
  final Product  product;
  final int      quantity;
  final double   subtotal;   // price × quantity
  final DateTime createdAt;
}

class Cart {
  final List<CartItem> items;
  final double  subtotalHt;
  final double  taxRate;
  final double  taxAmount;
  final double  subtotalTtc;
  final int     totalItems;
  final String  currency;
}
```

### 1.5 Commandes

```dart
class OrderItem {
  final int    id;
  final String productName;
  final String productDescription;
  final double soldePrice;
  final double regularPrice;
  final int    quantity;
  final double taxe;
  final double subTotalHt;
  final double subTotalTtc;
}

class Order {
  final int    id;
  final String clientName;
  final String billingAddress;
  final String shippingAddress;
  final int    quantity;
  final double taxe;
  final double orderCost;       // HT
  final double orderCostTtc;    // TTC (sans livraison)
  final bool   isPaid;
  final String carrierName;
  final double carrierPrice;
  final String paymentMethod;   // "moncash" | "stripe" | "natcash" | "Hors Ligne"
  final String? stripePaymentIntent;
  final String status;          // "pending"|"processing"|"shipped"|"delivered"|"canceled"
  final String statusDisplay;   // version lisible en français
  final List<OrderItem> orderDetails;
  final DateTime createdAt;
  final DateTime updatedAt;
}

// Suivi public — GET /orders/{id}/track/?email=
class OrderTracking {
  final int    id;
  final String status;
  final String statusDisplay;
  final bool   isPaid;
  final String paymentMethod;
  final String carrierName;
  final String shippingAddress;
  final int    itemsCount;
  final double orderCostTtc;
  final DateTime createdAt;
  final DateTime updatedAt;
}
```

### 1.6 Adresses

```dart
class Address {
  final int    id;
  final String name;         // label ex: "Maison"
  final String fullName;     // nom destinataire
  final String street;
  final String codePostal;
  final String city;
  final String country;
  final String phone;
  final String? moreDetails;
  final String adressType;   // "billing" | "shipping"
  final bool   isDefault;
  final DateTime createdAt;
  final DateTime updatedAt;
}
```

### 1.7 Avis

```dart
class Review {
  final int    id;
  final int    product;      // id produit (read-only)
  final int    author;       // id user (read-only)
  final String authorName;   // first_name + last_name ou username
  final int    rating;       // 1 à 5
  final String comment;
  final DateTime createdAt;
  final DateTime updatedAt;
}
```

### 1.8 Wishlist

```dart
class WishlistItem {
  final int     id;
  final Product product;
  final DateTime createdAt;
}
```

### 1.9 Paiement

```dart
// Réponse de POST /payments/initiate/
class PaymentInitResponse {
  final String  method;          // "moncash" | "stripe" | "natcash"
  final String? redirectUrl;     // MonCash/NatCash → ouvrir WebView
  final String? clientSecret;    // Stripe → PaymentSheet
  final int     orderId;
}
```

---

## 2. Navigation — carte des routes

```
/splash
│
├── /auth/login
│   └── /auth/register
│
└── /home  (BottomNav: Home | Shop | Cart | Profile)
    │
    ├── /home
    │   └── /products/:slug
    │       └── /reviews/:productId
    │
    ├── /shop
    │   ├── ?q=...          (recherche)
    │   ├── ?category=...   (filtre catégorie)
    │   └── /products/:slug
    │
    ├── /cart
    │   └── /checkout
    │       ├── /checkout/address      (étape 2)
    │       ├── /checkout/payment      (étape 1 — ou combiné)
    │       └── /checkout/confirm      (étape 4 — confirmation)
    │
    ├── /wishlist
    │
    └── /profile
        ├── /profile/edit
        ├── /profile/password
        ├── /profile/addresses
        │   └── /profile/addresses/new
        ├── /orders
        │   └── /orders/:id
        └── /track           (suivi public — accessible sans auth)
```

---

## 3. Écrans Auth

### SplashScreen `/splash`

**But :** Vérifie la présence des tokens → redirige vers `/home` ou `/auth/login`.

**Logique :**
```dart
final token = await secureStorage.read(key: 'access_token');
if (token != null && !JwtDecoder.isExpired(token)) {
  router.go('/home');
} else {
  // Tenter un refresh silencieux, sinon :
  router.go('/auth/login');
}
```

**UI :** Logo MatStore centré + fond gradient `#1a1a2e` + indicateur de chargement.

---

### LoginScreen `/auth/login`

**But :** Connexion par email ou username.

**API :** `POST /api/auth/login/`
```json
{ "username": "...", "password": "...", "fcm_token": "..." }
```
**Réponse :** `{ access, refresh, user: UserProfile }`

**UI :**
- Logo MatStore
- Champ email/username
- Champ mot de passe (masquable)
- Bouton "Se connecter"
- Lien → RegisterScreen
- Gestion erreur `INVALID_CREDENTIALS`

**Après login :** stocker tokens en `FlutterSecureStorage` → envoyer FCM token → `router.go('/home')`.

---

### RegisterScreen `/auth/register`

**But :** Création de compte.

**API :** `POST /api/auth/register/`
```json
{
  "username": "...", "email": "...",
  "first_name": "...", "last_name": "...",
  "password": "...", "password2": "...",
  "agree_terms": true
}
```
**Réponse :** `{ id, username, email, tokens: { access, refresh } }`

**UI :**
- Formulaire : prénom, nom, email, mot de passe × 2, case "J'accepte les conditions"
- Validation locale avant envoi (longueur mot de passe, emails identiques)
- Lien → LoginScreen

---

## 4. Écrans principaux (bottom nav)

**BottomNavigationBar (4 onglets) :**
```
🏠 Accueil | 🛍 Boutique | 🛒 Panier (badge count) | 👤 Profil
```

---

### HomeScreen `/home`

**But :** Vitrine — meilleures ventes, nouveautés, collections.

**API :**
- `GET /api/products/?in_stock=true&ordering=-created_at` (nouveautés)
- `GET /api/products/featured/`
- `GET /api/products/new-arrivals/`
- `GET /api/categories/`

**UI :**
- `AppBar` avec barre de recherche → `/shop?q=...`
- Section "Catégories" — scroll horizontal, chips
- Section "Nouveautés" — `ListView` horizontal de `ProductCard`
- Section "Produits vedettes" — grille 2 colonnes
- `ProductCard` : image (CachedNetworkImage + shimmer), nom, prix barré / prix solde, badge "Nouveau" ou "Promo"

**Navigation :** tap sur une `ProductCard` → `/products/:slug`.

---

### ShopListScreen `/shop`

**But :** Catalogue complet avec filtres et tri.

**API :** `GET /api/products/` avec query params :
```
?category=slug &min_price=x &max_price=y &in_stock=true
&search=mot &ordering=solde_price|-solde_price|created_at
&page=n
```

**UI :**
- `SearchBar` en haut (debounce 400 ms → `GET /api/products/search/?q=`)
- Chips de catégories (scroll horizontal)
- `FilterBottomSheet` : prix min/max, en stock seulement, tri
- Grille produits — `infinite_scroll_pagination` (`PagingController`)
- Shimmer pendant chargement
- État vide si aucun résultat

**Gestion pagination :**
```dart
// Réponse API : { success, count, next, previous, results: [...] }
_pagingController.appendPage(response.results, nextPage);
// ou appendLastPage si response.next == null
```

---

### CartScreen `/cart`

**But :** Voir et modifier le panier.

**API :**
- `GET /api/cart/`
- `PATCH /api/cart/update/{item_id}/` `{ "quantity": n }`
- `DELETE /api/cart/remove/{item_id}/`
- `DELETE /api/cart/clear/`

**UI :**
- `ListView` d'articles : image, nom, prix unitaire, sélecteur quantité +/−, bouton supprimer
- Bloc récapitulatif : sous-total HT, taxes, sous-total TTC, devise
- Bouton "Commander" → `/checkout` (désactivé si panier vide)
- Shimmer pendant chargement, état vide avec CTA → `/shop`

**Note :** Si utilisateur non connecté, afficher modal de connexion avant d'accéder au panier.

---

### ProfileScreen `/profile`

**But :** Accès rapide aux sections du compte.

**API :** `GET /api/auth/me/`

**UI :**
- Avatar initiales ou photo
- Nom + email
- Entrées liste : Mes commandes, Mes adresses, Modifier le profil, Changer mot de passe
- Bouton "Se déconnecter" → `POST /api/auth/logout/` + vider tokens + `router.go('/auth/login')`

---

## 5. Écrans Produits

### ProductDetailScreen `/products/:slug`

**But :** Fiche produit complète.

**API :**
- `GET /api/products/{slug}/`
- `GET /api/reviews/?product={id}` (avis)

**UI :**
- Carousel d'images (PageView + dots) avec zoom
- Nom, marque, prix TTC en orange `#ff5722`, prix barré grisé
- Badge "Stock faible" si `stockQuantity < 5`, "Épuisé" si `!inStock`
- Description (onglets : Description / Plus de détails / Infos)
- Sélecteur quantité + bouton "Ajouter au panier" → `POST /api/cart/add/`
- Bouton cœur "Wishlist" → `POST /api/wishlist/add/`
- Section avis : étoiles (1–5), liste `ReviewCard`, bouton "Laisser un avis" (si connecté + achat vérifié)
- Section "Produits similaires" — `ListView` horizontal depuis `GET /api/products/?category=slug`

**Erreurs à gérer :** `OUT_OF_STOCK`, `INSUFFICIENT_STOCK`.

---

### ReviewFormScreen (bottom sheet ou écran dédié)

**But :** Laisser un avis.

**API :** `POST /api/reviews/` `{ "product_id": n, "rating": 4, "comment": "..." }`

**Prérequis :** utilisateur connecté + achat vérifié (l'API retourne `403` sinon avec un message explicite).

**UI :**
- Sélecteur d'étoiles interactif (1–5)
- Zone de texte commentaire
- Bouton "Envoyer"

---

## 6. Flux Checkout

> Le checkout se fait en **4 étapes** (cohérent avec l'interface web) :
> 1. Méthode de paiement
> 2. Adresse de facturation / livraison
> 3. Mode de livraison *(non géré côté API actuellement — pas d'endpoint carrier)*
> 4. Confirmation / Paiement

---

### CheckoutScreen `/checkout`

**But :** Tunnel de commande complet.

**Architecture recommandée :** `PageView` ou `Stepper` avec 4 étapes, ou 4 écrans séparés reliés par GoRouter.

---

#### Étape 1 — PaymentMethodScreen

**But :** Choisir la méthode de paiement.

**Options toujours affichées :**
| Option | Condition d'affichage |
|--------|----------------------|
| Stripe | Toujours si clé publique disponible |
| MonCash | Toujours (si configuré côté back) |
| NatCash | Toujours |
| Hors Ligne | **Toujours** |

**UI :**
- Liste de cards à sélection unique (RadioListTile stylisé)
- Card MonCash : fond rouge `#e52329`, logo texte
- Card Hors Ligne : fond gris, icône reçu — affiche un champ upload `image_picker` si sélectionné

---

#### Étape 2 — AddressSelectionScreen

**But :** Choisir ou créer une adresse de livraison.

**API :**
- `GET /api/addresses/` — liste des adresses sauvegardées
- `POST /api/addresses/` — ajouter une nouvelle adresse

**UI :**
- Liste d'adresses existantes (cards sélectionnables)
- Bouton "+ Nouvelle adresse" → `AddressFormScreen` en bottom sheet
- Toggle "Adresse de livraison différente"

---

#### Étape 3 — (Livraison)

> Pas encore d'endpoint API pour les transporteurs (`/api/carriers/` à créer).
> En attendant : afficher les options disponibles en statique ou laisser l'utilisateur indiquer ses préférences dans un champ texte dans les notes de commande.

---

#### Étape 4 — OrderConfirmScreen `/checkout/confirm`

**But :** Récapitulatif final + lancer le paiement.

**API :** `POST /api/orders/`
```json
{
  "items": [{ "product_id": 1, "quantity": 2 }],
  "payment_method": "moncash",
  "delivery_address": { "street": "...", "city": "...", "department": "Ouest" },
  "notes": ""
}
```
**Réponse :** `Order` complet + `orderId` pour le paiement.

**Ensuite selon la méthode :**

```dart
switch (paymentMethod) {

  case 'stripe':
    // POST /api/payments/initiate/ → clientSecret
    await Stripe.instance.initPaymentSheet(
      paymentSheetParameters: SetupPaymentSheetParameters(
        paymentIntentClientSecret: clientSecret,
        merchantDisplayName: 'MatStore Haiti',
      ),
    );
    await Stripe.instance.presentPaymentSheet();
    // → POST /api/payments/verify/ pour confirmer
    break;

  case 'moncash':
    // POST /api/payments/initiate/ → redirectUrl
    // Ouvrir WebView, surveiller l'URL de retour
    // → POST /api/payments/verify/
    break;

  case 'offline':
    // Afficher dialog avec instructions + upload preuve (image_picker)
    // Soumettre avec multipart (endpoint à venir — voir recommandation_android.md)
    // → Afficher OfflineConfirmScreen
    break;
}
```

---

### OfflineConfirmScreen

**But :** Confirmation après commande hors ligne.

**UI :**
- Icône hourglass orange animée
- Titre "Commande enregistrée !"
- Texte : "MatStore Haiti vous contactera sous 24–48 h pour confirmer votre paiement."
- Timeline 3 étapes : Enregistrée → Vérification → Expédition
- Récapitulatif commande
- Bouton "Retour à l'accueil"

---

## 7. Écrans Commandes

### OrderListScreen `/orders`

**But :** Historique des commandes de l'utilisateur.

**API :** `GET /api/orders/`
Réponse paginée : `{ success, count, next, previous, results: [Order] }`

**UI :**
- `ListView` paginée avec `infinite_scroll_pagination`
- `OrderCard` : numéro commande, date, total TTC, statut (badge coloré), is_paid
- Couleurs des statuts :
  - `pending` → orange `#f59e0b`
  - `processing` → bleu `#3b82f6`
  - `shipped` → violet `#8b5cf6`
  - `delivered` → vert `#22c55e`
  - `canceled` → rouge `#ef4444`
- Tap → `OrderDetailScreen`

---

### OrderDetailScreen `/orders/:id`

**But :** Détail complet d'une commande.

**API :** `GET /api/orders/{id}/`

**UI :**
- En-tête : numéro, date, statut
- Table des articles (produit, qté, sous-total)
- Bloc adresses (facturation / livraison)
- Récapitulatif : sous-total HT, taxes, livraison, **total TTC**
- Bloc paiement : méthode, statut payé/en attente
- Bouton "Annuler" → `POST /api/orders/{id}/cancel/` (visible si `status == 'pending'`)
- Bouton "Suivre" → `OrderTrackingScreen`

---

### OrderTrackingScreen `/track`

**But :** Suivi public (sans authentification) — accessible depuis l'email de confirmation.

**API :** `GET /api/orders/{id}/track/?email={email}` (public, pas de Bearer token)

**UI :**
- Formulaire si accès direct : champ numéro commande + email
- Timeline de statut visuelle (4 étapes : Reçue → En traitement → Expédiée → Livrée)
- Étape active mise en surbrillance
- Infos affichées : statut, transporteur, adresse livraison, total, is_paid

---

## 8. Écrans Compte

### EditProfileScreen `/profile/edit`

**API :** `PATCH /api/auth/me/`
```json
{ "first_name": "...", "last_name": "...", "email": "...", "phone": "..." }
```

**UI :** Formulaire pré-rempli avec les données actuelles de `UserProfile`.

---

### ChangePasswordScreen `/profile/password`

**API :** `POST /api/auth/change-password/`
```json
{ "old_password": "...", "new_password": "...", "new_password2": "..." }
```

**UI :** 3 champs mot de passe (tous masquables), validation locale.

---

### AddressListScreen `/profile/addresses`

**API :**
- `GET /api/addresses/`
- `DELETE /api/addresses/{id}/`
- `PATCH /api/addresses/{id}/default/`

**UI :**
- Liste de cards adresses
- Badge "Par défaut" sur l'adresse `isDefault = true`
- Actions swipe : modifier, supprimer
- FAB "+ Ajouter"

---

### AddressFormScreen `/profile/addresses/new` (ou edit)

**API :**
- `POST /api/addresses/` (création)
- `PATCH /api/addresses/{id}/` (modification)

**Champs :**
```
name (label), full_name, street, city, code_postal, country, phone,
more_details (optionnel), adress_type (billing|shipping)
```

**UI :** Formulaire avec validation, sélecteur `adress_type` (Facturation / Livraison).

---

### WishlistScreen `/wishlist`

**API :**
- `GET /api/wishlist/`
- `DELETE /api/wishlist/remove/{id}/`

**UI :**
- Grille de `ProductCard` avec bouton cœur actif
- Tap sur la carte → `ProductDetailScreen`
- Swipe ou bouton pour retirer
- État vide avec CTA → `/shop`

---

## 9. Écrans Annexes

### FAQScreen

**Options :**
- **A — WebView** : `webview_flutter` sur `https://matstorehaiti.online/faq/` *(simple, pas de maintenance)*
- **B — Natif** : si un endpoint `/api/faq/` est créé, afficher `ExpansionTile` par question/réponse

**Recommandé à court terme :** Option A.

---

### ContactScreen

**Option :** WebView sur `https://matstorehaiti.online/contact/`
ou formulaire natif avec `POST` vers un endpoint à créer.

---

### AboutScreen / TermsScreen

WebView sur les pages correspondantes du site.

---

## 10. Providers Riverpod suggérés

```dart
// Auth
final authProvider          = StateNotifierProvider<AuthNotifier, AuthState>(...);
final userProfileProvider   = FutureProvider<UserProfile>(...);

// Produits
final productsProvider      = StateNotifierProvider.family<ProductsNotifier, ProductsState, ProductFilters>(...);
final productDetailProvider = FutureProvider.family<ProductDetail, String>((ref, slug) => ...);
final searchProvider        = StateNotifierProvider<SearchNotifier, SearchState>(...);

// Panier
final cartProvider          = StateNotifierProvider<CartNotifier, Cart?>(...);
final cartCountProvider     = Provider<int>((ref) => ref.watch(cartProvider)?.totalItems ?? 0);

// Commandes
final ordersProvider        = StateNotifierProvider<OrdersNotifier, OrdersState>(...);
final orderDetailProvider   = FutureProvider.family<Order, int>((ref, id) => ...);

// Wishlist
final wishlistProvider      = StateNotifierProvider<WishlistNotifier, List<WishlistItem>>(...);
final isInWishlistProvider  = Provider.family<bool, int>((ref, productId) {
  return ref.watch(wishlistProvider).any((w) => w.product.id == productId);
});

// Adresses
final addressesProvider     = StateNotifierProvider<AddressNotifier, List<Address>>(...);

// Avis
final reviewsProvider       = FutureProvider.family<List<Review>, int>((ref, productId) => ...);
```

---

## Palette de couleurs MatStore

| Rôle | Hex |
|------|-----|
| Primaire | `#ff5722` |
| Primaire foncé | `#e64a19` |
| Fond sombre (appBar, cards dark) | `#1a1a2e` |
| Fond page | `#f4f6f9` |
| Succès | `#22c55e` |
| Alerte / En attente | `#f59e0b` |
| Erreur | `#ef4444` |
| Texte principal | `#1a1a2e` |
| Texte secondaire | `#6c757d` |

```dart
// lib/core/theme/app_colors.dart
class AppColors {
  static const primary     = Color(0xFFFF5722);
  static const primaryDark = Color(0xFFE64A19);
  static const dark        = Color(0xFF1A1A2E);
  static const background  = Color(0xFFF4F6F9);
  static const success     = Color(0xFF22C55E);
  static const warning     = Color(0xFFF59E0B);
  static const error       = Color(0xFFEF4444);
  static const textPrimary = Color(0xFF1A1A2E);
  static const textMuted   = Color(0xFF6C757D);
}
```
