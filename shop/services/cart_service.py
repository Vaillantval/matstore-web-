from django.contrib import messages
from shop.models import Carrier, Setting, Product  # Importez vos mod�les ici


class CartService:
    @staticmethod
    def add_to_cart(request, product_id, quantity):
        cart = request.session.get("cart", {})
        product_id = str(product_id)

        if product_id in cart:
            cart[product_id] += quantity
        else:
            cart[product_id] = quantity

        request.session["cart"] = cart
        messages.success(request, f"Produit ajout� au panier.")

    @staticmethod
    def remove_from_cart(request, product_id, quantity):
        cart = request.session.get("cart", {})
        product_id = str(product_id)

        if product_id in cart:
            if cart[product_id] <= quantity:
                del cart[product_id]
            else:
                cart[product_id] -= quantity

        request.session["cart"] = cart
        messages.success(request, f"Produit supprim� du panier.")

    @staticmethod
    def clear_cart(request):
        request.session.pop("cart", None)
        messages.success(request, f"Le panier a �t� vid�.")

    @staticmethod
    def get_cart_details(request):
        cart = request.session.get("cart", {})
        setting = Setting.objects.first()
        tax_rate = setting.taxe_rate / 100 if setting else 0

        result = {
            "items": [],
            "sub_total": 0,
            "carrier_name": 0,
            "shipping_price": 0,
            "taxe_amount": 0,
            "sub_total_ht": 0,
            "sub_total_ttc": 0,
            "sub_total_with_shipping": 0,
            "cart_count": 0,
        }
        carrier = request.session.get("carrier")
        if not carrier:
            carrier = Carrier.objects.first()

        for product_id, quantity in cart.items():
            product = Product.objects.filter(id=product_id).first()

            if product:
                sub_total_ht  = product.solde_price * quantity
                taxe_amount   = sub_total_ht * tax_rate
                sub_total_ttc = sub_total_ht + taxe_amount
                result["items"].append(
                    {
                        "product": {
                            "id": product.id,
                            "slug": product.slug,
                            "name": product.name,
                            "description": product.description,
                            "solde_price": product.solde_price,
                            "regular_price": product.regular_price,
                            # Ajoutez d'autres attributs du produit ici
                        },
                        "quantity": quantity,
                        "sub_total": round(sub_total_ttc, 2),
                        "taxe_amount": round(taxe_amount, 2),
                        "sub_total_ht": round(sub_total_ht, 2),
                        "sub_total_ttc": round(sub_total_ttc, 2),
                    }
                )
                result["sub_total_ht"] += round(sub_total_ht, 2)
                result["cart_count"] += quantity

        result["taxe_amount"] = round(result["sub_total_ht"] * tax_rate, 2)
        result["sub_total_ttc"] = round(result["sub_total_ht"] * (1 + tax_rate), 2)
        result["sub_total"] = result["sub_total_ttc"]

        if carrier:
            result["carrier_name"] = carrier.name
            result["shipping_price"] = round(carrier.price, 2)
            result["sub_total_with_shipping"] = round(
                result["sub_total_ttc"] + carrier.price, 2
            )

        return result


# Valcin VAILLANT
# Modifié le 15/03/2026
