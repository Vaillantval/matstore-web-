from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from dashboard.models.Adress import Adress
from shop.models import Product, Category


@login_required(login_url='accounts:signin')
def overview(request):
    # Stats générales
    product_count  = Product.objects.count()
    category_count = Category.objects.count()

    # Données session
    cart     = request.session.get('cart', {})
    wishlist = request.session.get('wishlist', [])
    compare  = request.session.get('compare', [])

    cart_count     = sum(cart.values()) if isinstance(next(iter(cart.values()), None), int) else len(cart)
    wishlist_count = len(wishlist)
    compare_count  = len(compare)
    address_count  = Adress.objects.filter(author=request.user).count()

    # Produits en wishlist (pour affichage rapide)
    wishlist_products = (
        Product.objects
        .filter(id__in=wishlist)
        .prefetch_related('images')[:4]
    )

    return render(request, 'dashboard/overview.html', {
        'product_count':     product_count,
        'category_count':    category_count,
        'cart_count':        cart_count,
        'wishlist_count':    wishlist_count,
        'compare_count':     compare_count,
        'address_count':     address_count,
        'wishlist_products': wishlist_products,
    })
