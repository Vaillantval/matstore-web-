# MatStore Haiti — Guide FCM pour l'application Flutter

Guide complet des notifications push Firebase Cloud Messaging.
Toutes les notifications sont déclenchées automatiquement par le backend Django
via des signaux `post_save` — le frontend Flutter n'a rien à déclencher manuellement.

---

## Sommaire

1. [Architecture générale](#architecture-générale)
2. [Enregistrement du token FCM](#enregistrement-du-token-fcm)
3. [Types de notifications et payloads](#types-de-notifications-et-payloads)
4. [Gestion des 3 états de réception](#gestion-des-3-états-de-réception)
5. [Navigation au tap — écran par type](#navigation-au-tap--écran-par-type)
6. [Affichage in-app des notifications](#affichage-in-app-des-notifications)
7. [Récapitulatif des actions par type](#récapitulatif-des-actions-par-type)

---

## Architecture générale

```
Client Flutter                Backend Django              Firebase
──────────────                ──────────────              ────────
Login réussi
  │
  ├─ GET fcm_token ──────────────────────────────────────────────►
  │   (SDK Firebase)                                    Firebase retourne token
  │◄─────────────────────────────────────────────────────────────
  │
  ├─ POST /api/auth/fcm-token/
  │   { fcm_token: "..." } ──►  Sauvegarde token sur User
  │                             Abonne au topic "matstore"
  │                             Si staff → topic "admin" aussi
  │◄── { success: true } ───────
  │
  │   [Plus tard — événement métier]
  │
  │                             order.save() → signal post_save
  │                             → send_to_token(token, ...)
  │                                      ──────────────────────►
  │◄── Notification push ────────────────────────────────────────
```

---

## Enregistrement du token FCM

Appeler **impérativement après chaque login réussi**.

```dart
Future<void> registerFcmToken(String accessToken) async {
  // Demander la permission (Android 13+)
  final settings = await FirebaseMessaging.instance.requestPermission();
  if (settings.authorizationStatus != AuthorizationStatus.authorized) return;

  // Récupérer le token
  final fcmToken = await FirebaseMessaging.instance.getToken();
  if (fcmToken == null) return;

  // Envoyer au backend
  await dio.post(
    '/api/auth/fcm-token/',
    data: {'fcm_token': fcmToken},
    options: Options(
      headers: {'Authorization': 'Bearer $accessToken'},
    ),
  );
}
```

> Le token peut changer (réinstallation, effacement données).
> Toujours le renvoyer après un login, même si l'utilisateur avait déjà un compte.

---

## Types de notifications et payloads

Le champ `data['type']` identifie le type de notification.
Tous les champs `data` sont des **strings** (contrainte FCM).

---

### `new_order` — Commande reçue (client)

Déclencheur : client passe une commande via `POST /api/orders/`

```json
{
  "notification": {
    "title": "Commande recue",
    "body": "Votre commande #42 a bien ete enregistree."
  },
  "data": {
    "type": "new_order",
    "order_id": "42",
    "total": "1250.0",
    "status": "pending"
  }
}
```

**Affichage recommandé :**

```
┌─────────────────────────────────────────────┐
│  🛍️  Commande reçue                          │
│  ─────────────────────────────────────────  │
│  Votre commande #42 a bien été enregistrée. │
│                                             │
│  Total : 1 250,00 HTG                       │
│  Statut : En attente                        │
│                                             │
│  [ Voir ma commande ]                       │
└─────────────────────────────────────────────┘
```

**Navigation au tap :** `OrderDetailScreen(orderId: 42)`

---

### `order_status` — Changement de statut (client)

Déclencheur : admin change le statut depuis l'interface admin web ou l'app Flutter admin

```json
{
  "notification": {
    "title": "Commande expediee",
    "body": "Votre commande #42 est en route !"
  },
  "data": {
    "type": "order_status",
    "order_id": "42",
    "status": "shipped"
  }
}
```

**Statuts possibles et leur label :**

| `status` | Titre affiché | Icône |
|----------|--------------|-------|
| `processing` | Commande confirmée | ✅ |
| `shipped` | Commande expédiée | 🚚 |
| `delivered` | Commande livrée | 🎉 |
| `canceled` | Commande annulée | ❌ |

**Affichage recommandé (exemple : expédiée) :**

```
┌─────────────────────────────────────────────┐
│  🚚  Commande expédiée                       │
│  ─────────────────────────────────────────  │
│  Votre commande #42 est en route !          │
│                                             │
│  Statut actuel : Expédiée                   │
│                                             │
│  [ Suivre ma commande ]                     │
└─────────────────────────────────────────────┘
```

**Navigation au tap :** `OrderDetailScreen(orderId: 42)`

---

### `payment_verified` — Paiement offline confirmé (client)

Déclencheur : admin marque le `payment_status` à `verified` depuis l'interface Django admin

```json
{
  "notification": {
    "title": "Paiement confirme",
    "body": "Votre paiement pour la commande #42 a ete verifie."
  },
  "data": {
    "type": "payment_verified",
    "order_id": "42"
  }
}
```

**Affichage recommandé :**

```
┌─────────────────────────────────────────────┐
│  ✅  Paiement confirmé                       │
│  ─────────────────────────────────────────  │
│  Votre virement pour la commande #42        │
│  a été vérifié par notre équipe.            │
│                                             │
│  Votre commande est maintenant en cours     │
│  de traitement.                             │
│                                             │
│  [ Voir la commande ]                       │
└─────────────────────────────────────────────┘
```

**Navigation au tap :** `OrderDetailScreen(orderId: 42)`

---

### `new_product` — Nouveau produit disponible (tous les utilisateurs)

Déclencheur : admin crée un nouveau produit (`is_available = true`)
Envoyé via le **topic `matstore`** — tous les utilisateurs connectés le reçoivent.

```json
{
  "notification": {
    "title": "Nouveau produit disponible",
    "body": "Ciment Portland — 350.0 HTG"
  },
  "data": {
    "type": "new_product",
    "product_id": "15",
    "product_slug": "ciment-portland",
    "name": "Ciment Portland",
    "price": "350.0",
    "image": "product_images/2025/03/23/ciment.jpg"
  }
}
```

**Affichage recommandé :**

```
┌─────────────────────────────────────────────┐
│  🆕  Nouveau produit disponible              │
│  ─────────────────────────────────────────  │
│  [IMAGE]  Ciment Portland                   │
│           350,00 HTG                        │
│                                             │
│  [ Voir le produit ]    [ Ajouter au panier]│
└─────────────────────────────────────────────┘
```

**Navigation au tap :** `ProductDetailScreen(slug: 'ciment-portland')`

> L'URL de l'image est un chemin relatif. Construire l'URL complète :
> `${baseUrl}/media/${data['image']}`

---

### `new_order_admin` — Nouvelle commande (admins uniquement)

Déclencheur : client passe une commande.
Envoyé via le **topic `admin`** — uniquement les comptes staff.

```json
{
  "notification": {
    "title": "Nouvelle commande #42",
    "body": "Jean Dupont — 1250.0 HTG"
  },
  "data": {
    "type": "new_order_admin",
    "order_id": "42",
    "client_name": "Jean Dupont",
    "total": "1250.0",
    "payment_method": "moncash"
  }
}
```

**Affichage recommandé (vue admin) :**

```
┌─────────────────────────────────────────────┐
│  🛒  Nouvelle commande #42                   │
│  ─────────────────────────────────────────  │
│  Client : Jean Dupont                       │
│  Total  : 1 250,00 HTG                      │
│  Paiement : MonCash                         │
│                                             │
│  [ Voir la commande ]                       │
└─────────────────────────────────────────────┘
```

**Navigation au tap :** `AdminOrderDetailScreen(orderId: 42)`

---

### `proof_submitted` — Preuve de paiement soumise (admins uniquement)

Déclencheur : client uploade une preuve de paiement via `POST /api/payments/offline/`
Envoyé via le **topic `admin`**.

```json
{
  "notification": {
    "title": "Preuve de paiement recue",
    "body": "Commande #42 — Jean Dupont"
  },
  "data": {
    "type": "proof_submitted",
    "order_id": "42",
    "client": "Jean Dupont",
    "total": "1250.0"
  }
}
```

**Affichage recommandé (vue admin) :**

```
┌─────────────────────────────────────────────┐
│  🧾  Preuve de paiement reçue               │
│  ─────────────────────────────────────────  │
│  Commande #42 — Jean Dupont                 │
│  Montant : 1 250,00 HTG                     │
│                                             │
│  Une preuve de virement a été soumise.      │
│  Veuillez vérifier et valider.              │
│                                             │
│  [ Vérifier la preuve ]                     │
└─────────────────────────────────────────────┘
```

**Navigation au tap :** `AdminOrderDetailScreen(orderId: 42)`
(afficher directement l'image de la preuve et le bouton de validation)

---

## Gestion des 3 états de réception

```dart
class FcmService {
  static void initialize(BuildContext context) {
    // 1. Foreground — app ouverte
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      _showInAppNotification(context, message);
    });

    // 2. Background — app en arrière-plan, utilisateur tape la notif
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      _navigateFromData(context, message.data);
    });

    // 3. Terminated — app fermée, relancée par tap sur la notif
    FirebaseMessaging.instance.getInitialMessage().then((message) {
      if (message != null) {
        // Attendre que le widget tree soit prêt
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _navigateFromData(context, message.data);
        });
      }
    });
  }
}
```

---

## Navigation au tap — écran par type

```dart
void _navigateFromData(BuildContext context, Map<String, dynamic> data) {
  final type = data['type'] ?? '';
  final orderId = int.tryParse(data['order_id'] ?? '');
  final productSlug = data['product_slug'] ?? '';

  switch (type) {
    // Notifications client
    case 'new_order':
    case 'order_status':
    case 'payment_verified':
      if (orderId != null) {
        context.push('/orders/$orderId');
      }
      break;

    // Notifications produit
    case 'new_product':
      if (productSlug.isNotEmpty) {
        context.push('/products/$productSlug');
      }
      break;

    // Notifications admin
    case 'new_order_admin':
    case 'proof_submitted':
      if (orderId != null) {
        context.push('/admin/orders/$orderId');
      }
      break;

    default:
      // Aller à l'écran d'accueil par défaut
      context.go('/');
  }
}
```

---

## Affichage in-app des notifications

Pour le **foreground** (app ouverte), ne pas utiliser la notification système.
Afficher un **banner in-app** personnalisé :

```dart
void _showInAppNotification(BuildContext context, RemoteMessage message) {
  final type = message.data['type'] ?? '';
  final title = message.notification?.title ?? '';
  final body = message.notification?.body ?? '';

  showDialog(
    context: context,
    barrierColor: Colors.transparent,
    builder: (_) => Align(
      alignment: Alignment.topCenter,
      child: Material(
        color: Colors.transparent,
        child: Container(
          margin: const EdgeInsets.fromLTRB(16, 50, 16, 0),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 12)],
            border: Border(
              left: BorderSide(color: _colorForType(type), width: 4),
            ),
          ),
          child: Row(
            children: [
              Text(_iconForType(type), style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(title,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 4),
                    Text(body,
                        style: const TextStyle(
                            fontSize: 13, color: Colors.black54)),
                  ],
                ),
              ),
              GestureDetector(
                onTap: () {
                  Navigator.pop(context);
                  _navigateFromData(context, message.data);
                },
                child: const Icon(Icons.arrow_forward_ios,
                    size: 16, color: Colors.black38),
              ),
            ],
          ),
        ),
      ),
    ),
  );

  // Fermer automatiquement après 4 secondes
  Future.delayed(const Duration(seconds: 4), () {
    if (Navigator.canPop(context)) Navigator.pop(context);
  });
}

Color _colorForType(String type) {
  switch (type) {
    case 'new_order':        return const Color(0xFF4CAF50);
    case 'order_status':     return const Color(0xFF2196F3);
    case 'payment_verified': return const Color(0xFF4CAF50);
    case 'new_product':      return const Color(0xFFFF5722);
    case 'new_order_admin':  return const Color(0xFF333333);
    case 'proof_submitted':  return const Color(0xFFE63946);
    default:                 return const Color(0xFF9E9E9E);
  }
}

String _iconForType(String type) {
  switch (type) {
    case 'new_order':        return '🛍️';
    case 'order_status':     return '📦';
    case 'payment_verified': return '✅';
    case 'new_product':      return '🆕';
    case 'new_order_admin':  return '🛒';
    case 'proof_submitted':  return '🧾';
    default:                 return '🔔';
  }
}
```

---

## Récapitulatif des actions par type

| `type` | Destinataire | Écran cible | Action principale |
|--------|-------------|-------------|-------------------|
| `new_order` | Client | `OrderDetailScreen` | Voir le récapitulatif |
| `order_status` | Client | `OrderDetailScreen` | Voir le nouveau statut |
| `payment_verified` | Client | `OrderDetailScreen` | Voir la confirmation |
| `new_product` | Tous | `ProductDetailScreen` | Voir / Ajouter au panier |
| `new_order_admin` | Admin | `AdminOrderDetailScreen` | Traiter la commande |
| `proof_submitted` | Admin | `AdminOrderDetailScreen` | Vérifier et valider |

---

> Tous les champs du payload `data` sont des **strings**.
> Toujours parser avec `int.tryParse()` pour les IDs et `double.tryParse()` pour les montants.
> Ne jamais planter si un champ est absent — utiliser `data['field'] ?? ''`.
