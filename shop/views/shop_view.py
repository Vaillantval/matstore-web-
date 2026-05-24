import hashlib
import os
from django.core.cache import cache
from django.http import FileResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, InvalidPage
from django.db.models import Q

from shop.models import Slider, Collection, Product, Page, FAQ, ContactMessage, Category
from shop.models.Setting import Setting
from shop.forms import ContactForm
from shop.services.compare_service import CompareService

_SHOP_LIST_TTL    = 300   # 5 min
_PRODUCT_TTL      = 600   # 10 min
_CATEGORIES_TTL   = 600   # 10 min


class _FakePaginator:
    """Simule django.core.paginator.Paginator pour la compatibilité template."""
    def __init__(self, count, num_pages):
        self.count = count
        self.num_pages = num_pages
        self.page_range = range(1, num_pages + 1)


class _FakePage:
    """Simule django.core.paginator.Page pour la compatibilité template."""
    def __init__(self, object_list, number, paginator):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __iter__(self):
        return iter(self.object_list)

    def has_other_pages(self):
        return self.paginator.num_pages > 1

    def has_previous(self):
        return self.number > 1

    def has_next(self):
        return self.number < self.paginator.num_pages

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1


def _invalidate_shop_list_cache():
    """Supprime tous les caches shop_list et categories."""
    try:
        cache.delete_pattern('*shop_list_*')
    except AttributeError:
        pass
    cache.delete('shop_categories')


def index(request):
    sliders = Slider.objects.all()
    collections = Collection.objects.all()
    best_sellers = Product.objects.filter(is_best_seller=True)
    new_arrivals = Product.objects.filter(is_new_arrival=True)
    special_offers = Product.objects.filter(is_special_offer=True)
    featured = Product.objects.filter(is_featured=True)
    return render(
        request,
        "shop/index.html",
        {
            "sliders": sliders,
            "collections": collections,
            "best_sellers": best_sellers,
            "new_arrivals": new_arrivals,
            "featured": featured,
            "special_offers": special_offers,
        },
    )


def shop_list(request):
    category_slug = request.GET.get('category', '')
    filter_type   = request.GET.get('filter', '')
    sort          = request.GET.get('sort', 'newest')
    q             = request.GET.get('q', '').strip()
    page_number   = request.GET.get('page', '1')

    # ── Cache categories (partagé entre toutes les pages de boutique) ──────────
    categories = cache.get('shop_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('shop_categories', categories, _CATEGORIES_TTL)

    # ── Cache produits pour cette combinaison de filtres ──────────────────────
    filter_key = f'{category_slug}|{filter_type}|{sort}|{q}|{page_number}'
    list_cache_key = 'shop_list_' + hashlib.md5(filter_key.encode()).hexdigest()

    cached = cache.get(list_cache_key)
    if cached:
        return render(request, 'shop/shop_list.html', {**cached, 'categories': categories})

    # ── DB queries ────────────────────────────────────────────────────────────
    products = Product.objects.filter(is_available=True).prefetch_related('images', 'categories')

    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q)
        )
    if category_slug:
        products = products.filter(categories__slug=category_slug)
    if filter_type == 'best_seller':
        products = products.filter(is_best_seller=True)
    elif filter_type == 'new_arrival':
        products = products.filter(is_new_arrival=True)
    elif filter_type == 'special_offer':
        products = products.filter(is_special_offer=True)
    elif filter_type == 'featured':
        products = products.filter(is_featured=True)

    if sort == 'price_asc':
        products = products.order_by('solde_price')
    elif sort == 'price_desc':
        products = products.order_by('-solde_price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')

    paginator = Paginator(products, 6)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        page_obj = paginator.page(1)

    # Évalue les produits et leurs relations pour le cache (pickle)
    products_list = list(page_obj.object_list)
    for p in products_list:
        list(p.images.all())
        list(p.categories.all())

    active_category = next((c for c in categories if c.slug == category_slug), None)

    fake_page = _FakePage(
        object_list=products_list,
        number=page_obj.number,
        paginator=_FakePaginator(paginator.count, paginator.num_pages),
    )

    context = {
        'page_obj': fake_page,
        'active_category': active_category,
        'category_slug': category_slug,
        'filter_type': filter_type,
        'sort': sort,
        'q': q,
        'total': paginator.count,
    }
    cache.set(list_cache_key, context, _SHOP_LIST_TTL)

    return render(request, 'shop/shop_list.html', {**context, 'categories': categories})


def product_detail(request, slug):
    cache_key = f'product_detail_{slug}'
    cached = cache.get(cache_key)

    if cached:
        product, images, related = cached
    else:
        product = Product.objects.prefetch_related('images', 'categories').filter(slug=slug).first()
        if product is None:
            raise Http404()

        images = list(product.images.all())
        related = list(
            Product.objects.filter(
                categories__in=product.categories.all(), is_available=True
            ).exclude(pk=product.pk).prefetch_related('images', 'categories').distinct()[:8]
        )
        for r in related:
            list(r.images.all())
            list(r.categories.all())

        cache.set(cache_key, (product, images, related), _PRODUCT_TTL)

    discount = 0
    if product.regular_price > product.solde_price > 0:
        discount = round((product.regular_price - product.solde_price) / product.regular_price * 100)

    wishlist = request.session.get('wishlist', [])
    in_wishlist = product.pk in wishlist
    compare_ids = CompareService.get_compare(request)

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'images': images,
        'related': related,
        'discount': discount,
        'in_wishlist': in_wishlist,
        'compare_ids': compare_ids,
    })


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return redirect(f"{'/shop/'}?category={slug}")


def search_view(request):
    q = request.GET.get('q', '').strip()
    return redirect(f"{'/shop/'}?q={q}")


def about(request):
    page = Page.objects.filter(page_type='about').first()
    return render(request, "shop/about.html", {"page": page})


def contact(request):
    form = ContactForm()
    success = False

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
            )
            success = True
            form = ContactForm()

    return render(request, "shop/contact.html", {"form": form, "success": success})


def faq(request):
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, "shop/faq.html", {"faqs": faqs})


def terms(request):
    page = Page.objects.filter(page_type='terms').first()
    return render(request, "shop/terms.html", {"page": page})


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "shop/page_detail.html", {"page": page})


def download_apk(request):
    setting = Setting.objects.first()
    if not setting or not setting.apk_file:
        raise Http404("Aucun APK disponible pour le moment.")

    apk_path = setting.apk_file.path
    if not os.path.exists(apk_path):
        raise Http404("Fichier APK introuvable sur le serveur.")

    version = setting.apk_version or "latest"
    filename = f"MatStore-Haiti-v{version}.apk"

    response = FileResponse(
        open(apk_path, "rb"),
        content_type="application/vnd.android.package-archive",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Content-Length"] = os.path.getsize(apk_path)
    return response
