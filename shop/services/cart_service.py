from django.contrib import messages
from shop.models import Carrier, Product


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
        messages.success(request, "Produit ajouté au panier.")

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
        messages.success(request, "Produit supprimé du panier.")

    @staticmethod
    def clear_cart(request):
        request.session.pop("cart", None)
        messages.success(request, "Le panier a été vidé.")

    @staticmethod
    def get_cart_details(request):
        cart = request.session.get("cart", {})

        # Setting depuis le cache Redis (évite une query DB à chaque appel)
        from shop.templatetags.price_filters import _get_setting
        setting = _get_setting()
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

        if not cart:
            return result

        carrier_id = request.session.get("carrier_id")
        carrier = Carrier.objects.filter(id=carrier_id).first() if carrier_id else None

        # Charge tous les produits du panier en une seule query (fix N+1)
        products_map = {
            str(p.pk): p
            for p in Product.objects.filter(pk__in=cart.keys())
        }

        for product_id, quantity in cart.items():
            product = products_map.get(str(product_id))
            if not product:
                continue

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
            result["carrier_id"]              = carrier.id
            result["carrier_name"]            = carrier.name
            result["shipping_price"]          = round(carrier.price, 2)
            result["sub_total_with_shipping"] = round(result["sub_total_ttc"] + carrier.price, 2)
        else:
            result["sub_total_with_shipping"] = result["sub_total_ttc"]

        return result
