from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from dashboard.models.Adress import Adress
from shop.models import Product
from shop.models.Order import Order
from shop.cache_helpers import get_shop_counts


@login_required(login_url='accounts:signin')
def overview(request):
    counts = get_shop_counts()
    product_count  = counts['product_count']
    category_count = counts['category_count']

    cart     = request.session.get('cart', {})
    wishlist = request.session.get('wishlist', [])
    compare  = request.session.get('compare', [])

    cart_count     = sum(cart.values()) if isinstance(next(iter(cart.values()), None), int) else len(cart)
    wishlist_count = len(wishlist)
    compare_count  = len(compare)
    address_count  = Adress.objects.filter(author=request.user).count()

    wishlist_products = (
        Product.objects
        .filter(id__in=wishlist)
        .prefetch_related('images')[:4]
    )

    # Commandes du client
    order_count   = Order.objects.filter(author=request.user).count()
    recent_orders = Order.objects.filter(author=request.user).order_by('-created_at')[:3]

    return render(request, 'dashboard/overview.html', {
        'product_count':     product_count,
        'category_count':    category_count,
        'cart_count':        cart_count,
        'wishlist_count':    wishlist_count,
        'compare_count':     compare_count,
        'address_count':     address_count,
        'wishlist_products': wishlist_products,
        'order_count':       order_count,
        'recent_orders':     recent_orders,
    })


@login_required(login_url='accounts:signin')
def orders(request):
    user_orders = Order.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'dashboard/orders.html', {
        'orders': user_orders,
    })


@login_required(login_url='accounts:signin')
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, author=request.user)
    order_items = order.order_details.all()
    return render(request, 'dashboard/order_detail.html', {
        'order':       order,
        'order_items': order_items,
    })
