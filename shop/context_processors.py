from shop.models import Category, Collection
from shop.models.Setting import Setting

# from shop.models.Social import Social
from shop.models.Page import Page


def _migrate_cart_session(request):
    """Convertit l'ancien format {id: {dict}} vers le nouveau {id: qty}."""
    cart = request.session.get('cart', {})
    if cart and isinstance(next(iter(cart.values())), dict):
        cart = {k: v.get('qty', 1) for k, v in cart.items()}
        request.session['cart'] = cart
        request.session.modified = True
    return cart


def cart_context(request):
    """Injecte le panier et la wishlist dans tous les templates."""
    from shop.services.cart_service import CartService
    from shop.templatetags.price_filters import _get_setting, _get_rate, _format

    cart = _migrate_cart_session(request)
    wishlist = request.session.get('wishlist', [])
    cart_count = sum(cart.values()) if cart else 0

    if not cart:
        return {
            'cart_count': 0,
            'cart_header_items': [],
            'cart_header_subtotal': None,
            'wishlist_ids': wishlist,
            'wishlist_count': len(wishlist),
        }

    setting = _get_setting()
    items_preview = []
    cart_header_subtotal = None

    try:
        cart_details = CartService.get_cart_details(request)
        cart_count = cart_details['cart_count']
        preview = cart_details['items'][:4]

        product_ids = [item['product']['id'] for item in preview]
        from shop.models import Product as _Product
        products_map = {
            p.pk: p
            for p in _Product.objects.prefetch_related('images').filter(pk__in=product_ids)
        }

        for item in preview:
            prod = item['product']
            prod_obj = products_map.get(prod['id'])
            first_image = prod_obj.images.first() if prod_obj else None
            image_url = first_image.image.url if first_image else None

            if setting:
                rate = _get_rate(setting.base_currency, setting.currency)
                display_price = _format(prod['solde_price'] * rate, setting.currency)
            else:
                display_price = f"{prod['solde_price']:.2f}"

            items_preview.append({
                'product_id': prod['id'],
                'name': prod['name'],
                'slug': prod['slug'],
                'image': image_url,
                'display_price': display_price,
                'qty': item['quantity'],
            })

        subtotal = cart_details['sub_total']
        if setting:
            rate = _get_rate(setting.base_currency, setting.currency)
            cart_header_subtotal = _format(subtotal * rate, setting.currency)
        else:
            cart_header_subtotal = f"{subtotal:.2f}"

    except Exception:
        pass

    return {
        'cart_count': cart_count,
        'cart_header_items': items_preview,
        'cart_header_subtotal': cart_header_subtotal,
        'wishlist_ids': wishlist,
        'wishlist_count': len(wishlist),
    }


def site_settings(request):
    settings_obj = Setting.objects.first()
    head_pages = Page.objects.filter(is_head=True)
    foot_pages = Page.objects.filter(is_foot=True)
    mega_categories = Category.objects.filter(is_mega=True)
    mega_collections = Collection.objects.all()[:3]

    my_head_pages = []
    my_foot_pages = []
    my_mega_categories = []

    for category in mega_categories:
        products = category.product_set.all()
        product_arr = []
        for product in products:
            product_arr.append(
                {
                    "name": product.name,
                    "slug": product.slug,
                }
            )
        my_mega_categories.append(
            {
                "name": category.name,
                "slug": category.slug,
                "product": product_arr,
            }
        )

    for item in head_pages:
        my_head_pages.append({"name": item.name, "slug": item.slug})
    for item in foot_pages:
        my_foot_pages.append({"name": item.name, "slug": item.slug})

    if settings_obj is None:
        return {
            "head_pages": my_head_pages,
            "foot_pages": my_foot_pages,
            "my_mega_categories": my_mega_categories,
            "mega_collections": mega_collections,
        }

    context = {
        "site_name": settings_obj.name,
        "site_description": settings_obj.description,
        "site_email": settings_obj.email,
        "site_currency": settings_obj.currency,
        "site_base_currency": settings_obj.base_currency,
        "site_phone": settings_obj.phone,
        "site_street": settings_obj.street,
        "site_city": settings_obj.city,
        "site_code_postal": settings_obj.code_postal,
        "site_state": settings_obj.state,
        "site_copyright": settings_obj.copyright,
        "site_logo": settings_obj.logo,
        "head_pages": my_head_pages,
        "foot_pages": my_foot_pages,
        "my_mega_categories": my_mega_categories,
        "mega_collections": mega_collections,
    }

    return context
