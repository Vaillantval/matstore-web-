
from shop.models import Method
from django.conf import settings

class StripeService:
    def __init__(self):
        # Fix #1 : on exclut les méthodes désactivées (is_available=False)
        self.method = Method.objects.filter(name='Stripe', is_available=True).first()

    # Impl�mentez ici la logique de votre service
    def get_public_key(self):
        if self.method:
            return self.method.prod_public_key if not settings.DEBUG else self.method.test_public_key
        return None  # G�rer le cas o� la m�thode n'est pas trouv�e en base de donn�es

    def get_private_key(self):
        if self.method:
            return self.method.prod_private_key if not settings.DEBUG else self.method.test_private_key
        return None  # G�rer le cas o� la m�thode n'est pas trouv�e en base de donn�es

    