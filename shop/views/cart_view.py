from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from shop.models import Product, Carrier
from shop.services.cart_service import CartService
from shop.templatetags.price_filters import _get_setting, _get_rate, _format


def _migrate_cart_session(request):
    """Convertit l'ancien format {id: {dict}} vers le nouveau {id: qty}."""
    cart = request.session.get('cart', {})
    if cart and isinstance(next(iter(cart.values())), dict):
        cart = {k: v.get('qty', 1) for k, v in cart.items()}
        request.session['cart'] = cart
        request.session.modified = True
    return cart


def _display_price(price, setting):
    if setting:
        rate = _get_rate(setting.base_currency, setting.currency)
        return _format(price * rate, setting.currency)
    return f"{price:.2f}"


def _build_summary(cart_details, setting):
    """Construit le dict résumé avec tous les montants formatés."""
    has_carrier = bool(cart_details.get('carrier_name') and cart_details['carrier_name'] != 0)
    shipping_price = cart_details['shipping_price'] if has_carrier else 0
    # Sans carrier, le total = TTC (pas de frais de port à ajouter)
    total_raw = (cart_details['sub_total_ttc'] + shipping_price) if has_carrier else cart_details['sub_total_ttc']

    return {
        'sub_total_ht':            _display_price(cart_details['sub_total_ht'], setting),
        'taxe_amount':             _display_price(cart_details['taxe_amount'], setting),
        'sub_total_ttc':           _display_price(cart_details['sub_total_ttc'], setting),
        'carrier_name':            cart_details['carrier_name'] if has_carrier else None,
        'carrier_id':              cart_details.get('carrier_id'),
        'shipping_price':          _display_price(shipping_price, setting),
        'sub_total_with_shipping': _display_price(total_raw, setting),
        'has_carrier':             has_carrier,
        'shipping_is_free':        has_carrier and shipping_price == 0,
    }


def _get_wishlist(request):
    return request.session.get('wishlist', [])


def _save_wishlist(request, wishlist):
    request.session['wishlist'] = wishlist
    request.session.modified = True


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product.objects.prefetch_related('images'), pk=product_id
    )
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not product.is_available or product.stock == 0:
        if is_ajax:
            return JsonResponse(
                {'success': False, 'msg_type': 'error', 'message': 'Ce produit est indisponible.'},
                status=400,
            )
        return redirect(request.META.get('HTTP_REFERER', '/'))

    try:
        qty = max(1, int(request.POST.get('qty', 1)))
    except (ValueError, TypeError):
        qty = 1

    cart = _migrate_cart_session(request)
    current_qty = cart.get(str(product_id), 0)
    already_in_cart = current_qty > 0
    addable_qty = product.stock - current_qty

    # Stock déjà maxé
    if addable_qty <= 0:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'msg_type': 'warning',
                'already_in_cart': True,
                'message': f'"{product.name}" est déjà dans votre panier (stock maximum atteint).',
                'cart_count': sum(cart.values()),
            }, status=400)
        return redirect(request.META.get('HTTP_REFERER', '/'))

    qty_capped = qty > addable_qty
    qty = min(qty, addable_qty)
    CartService.add_to_cart(request, product_id, qty)

    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())

    if qty_capped:
        message = f'Seulement {product.stock} unité(s) disponible(s) pour « {product.name} ». Quantité ajustée.'
        msg_type = 'warning'
    elif already_in_cart:
        message = f'Quantité de "{product.name}" mise à jour dans votre panier.'
        msg_type = 'info'
    else:
        message = f'"{product.name}" ajouté au panier.'
        msg_type = 'success'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'already_in_cart': already_in_cart,
            'msg_type': msg_type,
            'message': message,
            'cart_count': cart_count,
        })
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    current_qty = cart.get(str(product_id), 0)
    if current_qty > 0:
        CartService.remove_from_cart(request, product_id, current_qty)

    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': cart_count})
    return redirect('cart')


@require_POST
def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)

    try:
        qty = int(request.POST.get('qty', 1))
    except (ValueError, TypeError):
        qty = 1

    stock_warning = None
    actual_qty = qty

    if qty <= 0:
        current_qty = cart.get(key, 0)
        CartService.remove_from_cart(request, product_id, current_qty)
        actual_qty = 0
    else:
        product = get_object_or_404(Product, pk=product_id)
        if qty > product.stock:
            stock_warning = f'Seulement {product.stock} unité(s) disponible(s) pour « {product.name} ».'
            qty = product.stock
        actual_qty = qty
        cart[key] = qty
        request.session['cart'] = cart
        request.session.modified = True

    setting = _get_setting()
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0

    line_total = None
    summary = None

    if cart:
        cart_details = CartService.get_cart_details(request)
        item = next(
            (i for i in cart_details['items'] if str(i['product']['id']) == key),
            None,
        )
        if item:
            line_total = _display_price(item['sub_total_ht'], setting)
        summary = _build_summary(cart_details, setting)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'line_total': line_total,
            'summary': summary,
            'actual_qty': actual_qty,
            'stock_warning': stock_warning,
        })
    return redirect('cart')


def cart_detail(request):
    setting = _get_setting()
    items = []
    summary = None

    # Ensure a default carrier is set in session
    if not request.session.get('carrier_id'):
        default = Carrier.objects.first()
        if default:
            request.session['carrier_id'] = default.id
            request.session.modified = True

    cart = _migrate_cart_session(request)
    if cart:
        cart_details = CartService.get_cart_details(request)
        product_ids = [item['product']['id'] for item in cart_details['items']]
        products_map = {
            p.pk: p
            for p in Product.objects.prefetch_related('images').filter(pk__in=product_ids)
        }

        for item in cart_details['items']:
            prod_data = item['product']
            prod_obj = products_map.get(prod_data['id'])
            first_image = prod_obj.images.first() if prod_obj else None
            image_url = first_image.image.url if first_image else None

            items.append({
                'product_id': prod_data['id'],
                'name': prod_data['name'],
                'slug': prod_data['slug'],
                'qty': item['quantity'],
                'image': image_url,
                'display_price': _display_price(prod_data['solde_price'], setting),
                'display_total': _display_price(item['sub_total_ht'], setting),
            })

        summary = _build_summary(cart_details, setting)

    carriers = list(Carrier.objects.all())

    # Pré-sélectionner le premier carrier si aucun en session (cohérent avec checkout)
    selected_carrier_id = request.session.get('carrier_id')
    if not selected_carrier_id and carriers:
        first = carriers[0]
        selected_carrier_id = first.id
        request.session['carrier_id'] = first.id
        request.session['carrier'] = {
            'id': first.id,
            'name': first.name,
            'price': float(first.price),
        }
        # Recalculer le résumé avec le carrier désormais en session
        if summary is not None:
            summary = _build_summary(CartService.get_cart_details(request), setting)

    return render(request, 'shop/cart.html', {
        'items': items,
        'summary': summary,
        'carriers': carriers,
        'selected_carrier_id': selected_carrier_id,
    })


@require_POST
def select_carrier(request):
    carrier_id = request.POST.get('carrier_id')
    carrier = get_object_or_404(Carrier, pk=carrier_id)

    request.session['carrier_id'] = carrier.id
    request.session.modified = True

    setting = _get_setting()
    cart_details = CartService.get_cart_details(request)
    summary = _build_summary(cart_details, setting)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'carrier_id': carrier.id,
            'carrier_name': carrier.name,
            'summary': summary,
        })
    return redirect('cart')


def wishlist_detail(request):
    wishlist = _get_wishlist(request)
    setting = _get_setting()
    items = []

    if wishlist:
        products = (
            Product.objects
            .prefetch_related('images', 'categories')
            .filter(pk__in=wishlist)
        )
        for product in products:
            first_image = product.images.first()
            items.append({
                'product_id': product.pk,
                'name': product.name,
                'slug': product.slug,
                'image': first_image.image.url if first_image else None,
                'display_price': _display_price(product.solde_price, setting),
                'display_regular': (
                    _display_price(product.regular_price, setting)
                    if product.regular_price > product.solde_price else None
                ),
                'is_available': product.is_available and product.stock > 0,
                'categories': list(product.categories.values('name', 'slug')),
            })

    return render(request, 'shop/wishlist.html', {'items': items})


@require_POST
def clear_wishlist(request):
    _save_wishlist(request, [])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('wishlist')


@require_POST
def toggle_wishlist(request, product_id):
    wishlist = _get_wishlist(request)
    product_id = int(product_id)

    if product_id in wishlist:
        wishlist.remove(product_id)
        in_wishlist = False
    else:
        get_object_or_404(Product, pk=product_id)
        wishlist.append(product_id)
        in_wishlist = True

    _save_wishlist(request, wishlist)
    wishlist_count = len(wishlist)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'wishlist_count': wishlist_count,
        })
    return redirect(request.META.get('HTTP_REFERER', '/'))
