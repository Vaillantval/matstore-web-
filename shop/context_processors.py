from shop.models import Category, Collection
from shop.models.Setting import Setting
from shop.models.Page import Page

_SITE_CTX_TTL = 3600  # 1h — invalidé par signal sur Setting/Category/Page/Collection


def _migrate_cart_session(request):
    cart = request.session.get('cart', {})
    if cart and isinstance(next(iter(cart.values())), dict):
        cart = {k: v.get('qty', 1) for k, v in cart.items()}
        request.session['cart'] = cart
        request.session.modified = True
    return cart


def cart_context(request):
    if request.path.startswith('/admin/'):
        return {}

    from shop.services.cart_service import CartService
    from shop.templatetags.price_filters import _get_setting, _get_rate, _format

    cart = _migrate_cart_session(request)
    wishlist = request.session.get('wishlist', [])
    compare = request.session.get('compare', [])
    cart_count = sum(cart.values()) if cart else 0

    if not cart:
        return {
            'cart_count': 0,
            'cart_header_items': [],
            'cart_header_subtotal': None,
            'wishlist_ids': wishlist,
            'wishlist_count': len(wishlist),
            'compare_ids': compare,
            'compare_count': len(compare),
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
            first_image = (prod_obj.images.all()[0] if prod_obj and prod_obj.images.all() else None)
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
        'compare_ids': compare,
        'compare_count': len(compare),
    }


def site_settings(request):
    if request.path.startswith('/admin/'):
        return {}

    from django.core.cache import cache

    cached = cache.get('site_settings_ctx')
    if cached is not None:
        return cached

    try:
        settings_obj = Setting.objects.first()
        # prefetch_related élimine le N+1 sur les produits des mega catégories
        mega_categories = Category.objects.filter(is_mega=True).prefetch_related('product_set')
        head_pages = list(Page.objects.filter(is_head=True).values('name', 'slug'))
        foot_pages = list(Page.objects.filter(is_foot=True).values('name', 'slug'))
        mega_collections = list(Collection.objects.all()[:3])
    except Exception:
        return {}

    my_mega_categories = []
    for category in mega_categories:
        my_mega_categories.append({
            'name': category.name,
            'slug': category.slug,
            'product': [
                {'name': p.name, 'slug': p.slug}
                for p in category.product_set.all()
            ],
        })

    if settings_obj is None:
        ctx = {
            'head_pages': head_pages,
            'foot_pages': foot_pages,
            'my_mega_categories': my_mega_categories,
            'mega_collections': mega_collections,
            'show_app_banner': False,
        }
        cache.set('site_settings_ctx', ctx, _SITE_CTX_TTL)
        return ctx

    ctx = {
        'site_name': settings_obj.name,
        'site_description': settings_obj.description,
        'site_email': settings_obj.email,
        'site_currency': settings_obj.currency,
        'site_base_currency': settings_obj.base_currency,
        'site_phone': settings_obj.phone,
        'site_street': settings_obj.street,
        'site_city': settings_obj.city,
        'site_code_postal': settings_obj.code_postal,
        'site_state': settings_obj.state,
        'site_copyright': settings_obj.copyright,
        'site_logo': settings_obj.logo,
        'head_pages': head_pages,
        'foot_pages': foot_pages,
        'my_mega_categories': my_mega_categories,
        'mega_collections': mega_collections,
        'show_app_banner': settings_obj.show_app_banner and bool(settings_obj.apk_file),
        'apk_version': settings_obj.apk_version,
        'apk_description': settings_obj.apk_description,
    }
    cache.set('site_settings_ctx', ctx, _SITE_CTX_TTL)
    return ctx
