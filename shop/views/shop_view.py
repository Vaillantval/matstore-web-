from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, InvalidPage
from django.db.models import Q

from shop.models import Slider, Collection, Product, Page, FAQ, ContactMessage, Category
from shop.models.Setting import Setting
from shop.forms import ContactForm
from shop.services.compare_service import CompareService


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
    products = Product.objects.filter(is_available=True).prefetch_related('images', 'categories')
    categories = Category.objects.all()

    # Filtres GET
    category_slug = request.GET.get('category', '')
    filter_type   = request.GET.get('filter', '')
    sort          = request.GET.get('sort', 'newest')
    q             = request.GET.get('q', '').strip()

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q))

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
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        page_obj = paginator.page(1)

    active_category = categories.filter(slug=category_slug).first() if category_slug else None

    return render(request, 'shop/shop_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'active_category': active_category,
        'category_slug': category_slug,
        'filter_type': filter_type,
        'sort': sort,
        'q': q,
        'total': paginator.count,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'categories'), slug=slug)
    images = product.images.all()
    related = Product.objects.filter(
        categories__in=product.categories.all(), is_available=True
    ).exclude(pk=product.pk).prefetch_related('images', 'categories').distinct()[:8]

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
