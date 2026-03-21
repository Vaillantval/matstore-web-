from django.db import migrations


DEFAULT_FAQS = [
    (1,  "Comment puis-je passer une commande ?",
         "Parcourez notre catalogue, ajoutez les articles souhaités au panier, puis cliquez sur « Commander ». "
         "Suivez les étapes du processus de paiement : choisissez votre méthode de paiement, renseignez votre adresse de livraison, sélectionnez un mode de livraison et confirmez. Vous recevrez un email de confirmation dès validation."),

    (2,  "Quels modes de paiement acceptez-vous ?",
         "Nous acceptons plusieurs méthodes de paiement :\n"
         "• Carte bancaire via Stripe (Visa, Mastercard…)\n"
         "• MonCash (paiement mobile Digicel)\n"
         "• Paiement hors ligne (virement bancaire, dépôt ou remise en main propre — une preuve de paiement vous sera demandée).\n"
         "Toutes les transactions en ligne sont sécurisées."),

    (3,  "Quels sont les délais de livraison ?",
         "Les délais varient selon le mode de livraison choisi et votre localisation. "
         "En général, comptez 2 à 5 jours ouvrables pour Port-au-Prince et environs, et 5 à 10 jours pour les provinces. "
         "Vous pouvez consulter les options disponibles et leurs tarifs lors du checkout."),

    (4,  "Comment suivre ma commande ?",
         "Après validation de votre commande, connectez-vous à votre compte et rendez-vous dans « Mon espace » → « Mes commandes ». "
         "Vous y trouverez le statut en temps réel (En attente, En cours, Expédiée, Livrée). "
         "Un email vous est envoyé à chaque changement de statut."),

    (5,  "Puis-je modifier ou annuler ma commande ?",
         "Vous pouvez demander une modification ou annulation tant que votre commande est au statut « En attente ». "
         "Contactez-nous rapidement via le formulaire de contact ou par téléphone. "
         "Une fois la commande expédiée, l'annulation n'est plus possible."),

    (6,  "Quelle est votre politique de retour ?",
         "Vous disposez de 30 jours à compter de la réception pour retourner un article non utilisé et dans son emballage d'origine. "
         "Les frais de retour sont à la charge du client, sauf en cas d'erreur de notre part ou d'article défectueux. "
         "Contactez notre service client pour initier un retour."),

    (7,  "Que faire si je reçois un article endommagé ou incorrect ?",
         "Si votre colis arrive endommagé ou si vous recevez un mauvais article, contactez-nous dans les 48 h suivant la réception "
         "en joignant des photos du problème. Nous procéderons à un remplacement ou un remboursement sans frais supplémentaires."),

    (8,  "La livraison est-elle gratuite ?",
         "Oui, la livraison est offerte à partir d'un certain montant d'achat (consultez nos conditions actuelles sur le site). "
         "En dessous de ce seuil, des frais de livraison sont calculés selon le transporteur et la destination, et affichés clairement lors du checkout."),

    (9,  "Comment créer un compte client ?",
         "Cliquez sur l'icône « Compte » en haut à droite, puis sur « S'inscrire ». "
         "Renseignez votre email et un mot de passe. Vous pouvez aussi passer commande en tant qu'invité — un compte sera créé automatiquement avec votre email."),

    (10, "Mes informations personnelles sont-elles en sécurité ?",
         "Oui. Nous ne partageons jamais vos données avec des tiers à des fins commerciales. "
         "Les paiements en ligne sont traités par Stripe (certifié PCI-DSS) et MonCash — MatStore Haiti ne stocke aucune donnée de carte bancaire. "
         "Consultez notre politique de confidentialité pour plus de détails."),

    (11, "Comment utiliser le paiement hors ligne ?",
         "Sélectionnez « Paiement Hors Ligne » lors du checkout. "
         "Effectuez votre virement ou dépôt sur le compte MatStore Haiti, puis uploadez une photo ou capture d'écran de la preuve de paiement. "
         "Notre équipe vérifiera le paiement sous 24 à 48 h et vous contactera pour confirmer votre commande."),

    (12, "Comment contacter le service client ?",
         "Vous pouvez nous joindre via le formulaire de contact sur le site, par email à info@matstorehaiti.online, "
         "ou par téléphone du lundi au samedi de 9h à 18h (heure d'Haïti). "
         "Nous nous efforçons de répondre dans les 24 h ouvrables."),
]


def add_default_faqs(apps, schema_editor):
    FAQ = apps.get_model('shop', 'FAQ')
    # N'insère que si la table est vide pour ne pas dupliquer
    if FAQ.objects.exists():
        return
    for order, question, answer in DEFAULT_FAQS:
        FAQ.objects.create(
            question=question,
            answer=answer,
            order=order,
            is_active=True,
        )


def remove_default_faqs(apps, schema_editor):
    FAQ = apps.get_model('shop', 'FAQ')
    questions = [q for _, q, _ in DEFAULT_FAQS]
    FAQ.objects.filter(question__in=questions).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0012_order_payment_proof'),
    ]

    operations = [
        migrations.RunPython(add_default_faqs, remove_default_faqs),
    ]
