from django.shortcuts import render

from shop.models import Slider, Collection, Product


def index(request):
    sliders = Slider.objects.all()
    collections = Collection.objects.all()
    best_sellers = Product.objects.filter(is_best_seller=True)
    new_arrivals = Product.objects.filter(is_new_arrival=True)
    special_offers = Product.objects.filter(is_special_offer=True)
    featured = Product.objects.filter(is_featured=True)
    return render(request, 'shop/index.html', {'sliders': sliders, 'collections': collections, 'best_sellers': best_sellers, 'new_arrivals': new_arrivals,'featured': featured, 'special_offers': special_offers })