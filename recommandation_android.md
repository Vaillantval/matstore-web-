# Recommandations Flutter Android — MatStore Haiti

---

## 1. Packages recommandés

```yaml
dependencies:
  # HTTP & API
  dio: ^5.7.0                        # Client HTTP avec intercepteurs
  retrofit: ^4.4.1                   # Génération de client API typé
  pretty_dio_logger: ^1.4.0          # Log des requêtes en dev

  # Auth & stockage sécurisé
  flutter_secure_storage: ^9.2.2     # Stocker access + refresh token (Android Keystore)
  jwt_decoder: ^2.0.1                # Lire/vérifier l'expiration du token

  # State management
  flutter_riverpod: ^2.6.1           # Recommandé : simple, testable, scalable
  # OU bloc: ^8.1.4 si tu préfères BLoC

  # Navigation
  go_router: ^14.6.2                 # Navigation déclarative avec redirection auth

  # Images
  cached_network_image: ^3.4.1       # Cache des images produits
  image_picker: ^1.1.2               # Upload d'images (back office)

  # Paiements
  flutter_stripe: ^11.1.0            # SDK Stripe officiel Flutter
  url_launcher: ^6.3.1               # Redirection vers MonCash (WebView ou navigateur)
  webview_flutter: ^4.10.0           # WebView pour page de paiement MonCash

  # Push notifications
  firebase_messaging: ^15.1.4        # FCM pour les notifications push
  flutter_local_notifications: ^18.0.1

  # UX & UI
  shimmer: ^3.0.0                    # Skeleton loading pendant le chargement
  pull_to_refresh_flutter3: ^2.0.2   # Pull-to-refresh sur les listes
  infinite_scroll_pagination: ^4.1.0 # Pagination automatique (produits, commandes)
  fluttertoast: ^8.2.9               # Messages toast rapides

  # Utilitaires
  intl: ^0.20.1                      # Formatage des prix (HTG, USD)
  connectivity_plus: ^6.1.1          # Détecter si hors ligne
  shared_preferences: ^2.3.3         # Préférences légères (thème, langue)
  fl_chart: ^0.69.0                  # Graphes (back office admin — dashboard, rapports)

  # Modèles immuables & sérialisation JSON
  freezed_annotation: ^2.4.4         # Annotations pour classes immuables
  json_annotation: ^4.9.0            # Annotations pour fromJson/toJson

dev_dependencies:
  build_runner: ^2.4.13              # Génération de code (lancer : dart run build_runner build)
  freezed: ^2.5.7                    # Génère copyWith, ==, toString sur les modèles
  json_serializable: ^6.8.0          # Génère fromJson / toJson
```

**Usage :**
```dart
// Déclarer un modèle
@freezed
class Product with _$Product {
  const factory Product({
    required int id,
    required String name,
    required double price,
    @JsonKey(name: 'in_stock') required bool inStock,
  }) = _Product;

  factory Product.fromJson(Map<String, dynamic> json) => _$ProductFromJson(json);
}

// Régénérer après modification :
// dart run build_runner build --delete-conflicting-outputs
```

---

## 2. Gestion des tokens JWT

C'est la partie la plus critique. L'API utilise access token (1 jour) + refresh token (30 jours).

### Intercepteur Dio — à créer obligatoirement

```dart
// lib/core/network/auth_interceptor.dart
class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  final Dio _dio;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Token expiré → tenter le refresh automatique
      final refreshed = await _tryRefresh();
      if (refreshed) {
        // Rejouer la requête originale
        return handler.resolve(await _retry(err.requestOptions));
      }
      // Refresh échoué → déconnecter l'utilisateur
      await _logout();
    }
    handler.next(err);
  }
}
```

### Stockage sécurisé
```dart
// NE PAS utiliser SharedPreferences pour les tokens
// Utiliser flutter_secure_storage (Android Keystore)
const storage = FlutterSecureStorage(
  aOptions: AndroidOptions(encryptedSharedPreferences: true),
);
await storage.write(key: 'access_token', value: token);
await storage.write(key: 'refresh_token', value: refresh);
```

---

## 3. Paiements

### MonCash — Flux WebView
MonCash redirige vers une page web externe. Ne pas essayer d'intégrer nativement.

```dart
// 1. Appeler POST /api/payments/initiate/ → obtenir redirect_url
// 2. Ouvrir un WebView avec la redirect_url
// 3. Surveiller l'URL de retour pour détecter succès/échec
// 4. Appeler POST /api/payments/verify/ pour confirmer

WebViewWidget(
  controller: WebViewController()
    ..setNavigationDelegate(NavigationDelegate(
      onNavigationRequest: (request) {
        if (request.url.contains('matstorehaiti.online/success')) {
          // Paiement réussi → vérifier côté API
          verifyPayment();
          return NavigationDecision.prevent;
        }
        return NavigationDecision.navigate;
      },
    ))
    ..loadRequest(Uri.parse(redirectUrl)),
)
```

### Stripe — SDK Flutter
```dart
// Utiliser flutter_stripe directement
await Stripe.instance.initPaymentSheet(
  paymentSheetParameters: SetupPaymentSheetParameters(
    paymentIntentClientSecret: clientSecret, // vient de /api/payments/initiate/
    merchantDisplayName: 'MatStore Haiti',
  ),
);
await Stripe.instance.presentPaymentSheet();
```

### NatCash
NatCash ne fournit pas de SDK Flutter/mobile. Afficher un dialog avec les instructions
(`*202#`) et la référence de commande. L'admin confirme manuellement via le back office.

### Paiement Hors Ligne (virement / dépôt)
Cette méthode est actuellement disponible sur l'**interface web uniquement** (endpoint `/checkout/offline-pay/`, session Django). Elle n'est pas encore exposée comme endpoint REST.

**Options pour l'app Flutter :**

**Option A — Renvoyer vers le web** _(recommandée à court terme)_
```dart
// Ouvrir le checkout web dans un navigateur ou WebView
await launchUrl(Uri.parse('https://matstorehaiti.online/checkout/'));
```

**Option B — Implémenter côté API** _(quand l'endpoint sera ajouté)_
```dart
// Soumettre la commande + preuve de paiement en multipart
final formData = FormData.fromMap({
  'order_id': orderId,
  'payment_proof': await MultipartFile.fromFile(
    imagePath,
    filename: 'proof.jpg',
    contentType: MediaType('image', 'jpeg'),
  ),
});
await dio.post('/api/payments/offline/', data: formData);
// L'ordre sera marqué payment_method='Hors Ligne', is_paid=false
// Le client reçoit un email de confirmation avec délai 24-48h
```

**UX recommandée (Option B) :**
- Afficher un `image_picker` pour sélectionner la preuve
- Expliquer clairement le délai de vérification (24–48 h)
- Après soumission, afficher un écran de confirmation similaire à `offline_confirm.html`

---

## 4. Push Notifications (FCM)

L'API a un endpoint dédié `POST /api/auth/fcm-token/` pour enregistrer le token.

> **Important :** Ne pas inclure `fcm_token` dans le payload de `POST /auth/login/`.
> Le login ne retourne que `{ access, refresh, user }`. Le FCM token est envoyé
> **séparément**, juste après, via l'endpoint dédié ci-dessous.

```dart
// Après login réussi, envoyer le token via l'endpoint dédié
final fcmToken = await FirebaseMessaging.instance.getToken();

await apiClient.post('/api/auth/fcm-token/', {'fcm_token': fcmToken});

// Écouter les refresh de token (Android régénère le token parfois)
FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
  apiClient.post('/api/auth/fcm-token/', {'fcm_token': newToken});
});
```

**Pourquoi un endpoint dédié plutôt que PATCH /me/ ?**
- Appelable sans recharger tout le profil
- Idempotent : peut être appelé à chaque démarrage de l'app sans risque
- Fonctionne même si l'utilisateur n'a pas modifié son profil

**Notifications utiles à implémenter côté backend :**
- Changement de statut commande (signal existant → ajouter envoi FCM)
- Confirmation de paiement reçu

---

## 5. Recherche & Suivi de commande

### Recherche full-text
L'endpoint dédié `/api/products/search/?q=` cherche dans le nom, description, marque et catégories.
Différent du `?search=` sur la liste produits qui est plus limité.

```dart
// Barre de recherche — debounce 400ms recommandé pour éviter trop de requêtes
onChanged: (query) {
  debounce(() => apiClient.get('/api/products/search/?q=$query'));
}
```

### Suivi de commande public
L'endpoint `GET /api/orders/{id}/track/?email=` est **sans authentification**.
Utile pour une page "Suivre ma commande" accessible depuis l'email de confirmation.

```dart
// Page de suivi accessible sans être connecté
final tracking = await apiClient.get(
  '/api/orders/$orderId/track/?email=$email',
  requiresAuth: false,  // pas de Bearer token
);
// Retourne : statut, is_paid, transporteur, adresse livraison, total
```

---

## 6. Pagination

L'API retourne ce format pour toutes les listes :
```json
{
  "success": true,
  "count": 150,
  "next": "https://.../api/products/?page=2",
  "previous": null,
  "results": [...]
}
```

Utiliser `infinite_scroll_pagination` pour les listes produits et commandes :
```dart
final _pagingController = PagingController<int, Product>(firstPageKey: 1);

_pagingController.addPageRequestListener((pageKey) async {
  final response = await api.getProducts(page: pageKey);
  final isLastPage = response.next == null;
  if (isLastPage) {
    _pagingController.appendLastPage(response.results);
  } else {
    _pagingController.appendPage(response.results, pageKey + 1);
  }
});
```

---

## 7. Gestion des erreurs API

L'API retourne toujours un `error.code` standardisé. Créer un mapper centralisé :

```dart
// lib/core/network/api_error.dart
class ApiException implements Exception {
  final String code;
  final String message;
}

// Dans le dio intercepteur
String _friendlyMessage(String code) => switch (code) {
  'OUT_OF_STOCK'         => 'Ce produit est épuisé.',
  'INSUFFICIENT_STOCK'   => 'Stock insuffisant.',
  'ORDER_NOT_CANCELLABLE'=> 'Cette commande ne peut plus être annulée.',
  'PAYMENT_FAILED'       => 'Le paiement a échoué.',
  'INVALID_CREDENTIALS'  => 'Email ou mot de passe incorrect.',
  'TOKEN_EXPIRED'        => 'Session expirée, veuillez vous reconnecter.',
  _                      => 'Une erreur est survenue.',
};
```

---

## 8. Structure du projet Flutter recommandée

```
lib/
├── core/
│   ├── network/          # Dio, intercepteurs, ApiClient
│   ├── storage/          # SecureStorage wrapper
│   ├── router/           # GoRouter + guards auth
│   └── theme/            # Couleurs, typographie MatStore
│
├── features/
│   ├── auth/             # Login, register, profil
│   ├── products/         # Liste, détail, recherche, filtres
│   ├── cart/             # Panier
│   ├── orders/           # Commandes, suivi
│   ├── payments/         # MonCash WebView, Stripe sheet
│   ├── wishlist/         # Favoris
│   ├── addresses/        # Gestion adresses
│   └── reviews/          # Avis produits
│
└── shared/
    ├── widgets/          # Boutons, cards, loaders communs
    └── utils/            # Formatage prix HTG, dates
```

---

## 9. Points Android spécifiques

### `AndroidManifest.xml` — permissions nécessaires
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
<!-- Pour les notifications push -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
<!-- Pour l'upload d'images (back office) -->
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>
```

### Cleartext traffic (dev uniquement)
Si tu testes sur `http://` en local, ajouter dans `AndroidManifest.xml` :
```xml
android:usesCleartextTraffic="true"  <!-- RETIRER en production -->
```

### Taille des images produits
Les images viennent de Railway (`/media/product_images/...`). Utiliser
`cached_network_image` avec un `maxWidth` pour ne pas charger de trop grandes images :
```dart
CachedNetworkImage(
  imageUrl: imageUrl,
  memCacheWidth: 600,   // limite la mémoire utilisée
  placeholder: (_, __) => Shimmer.fromColors(...),
)
```

---

## 10. Formatage des prix

Les prix sont en **HTG (Gourdes haïtiennes)**. L'API retourne un float brut.

```dart
// lib/shared/utils/price_formatter.dart
String formatPrice(double amount, String currency) {
  final formatted = NumberFormat('#,##0.00', 'fr_HT').format(amount);
  return currency == 'HTG' ? '$formatted G' : '$currency $formatted';
}
// Exemple : "1 250,00 G"
```

---

## 11. Mode hors ligne minimal

```dart
// Vérifier la connexion avant chaque requête critique
final connectivity = await Connectivity().checkConnectivity();
if (connectivity == ConnectivityResult.none) {
  // Afficher banner "Pas de connexion"
  // Servir depuis le cache Dio si disponible
}
```

Configurer Dio avec un cache simple pour les produits et catégories
(données qui changent peu) en utilisant `dio_cache_interceptor`.
