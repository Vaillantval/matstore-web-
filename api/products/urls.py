from django.urls import path

from api.products.views import (
    FeaturedProductsView,
    NewArrivalsView,
    OnSaleProductsView,
    ProductDetailView,
    ProductListView,
    ProductSearchView,
)

urlpatterns = [
    path("", ProductListView.as_view(), name="api-product-list"),
    path("search/", ProductSearchView.as_view(), name="api-product-search"),
    path("featured/", FeaturedProductsView.as_view(), name="api-product-featured"),
    path("new-arrivals/", NewArrivalsView.as_view(), name="api-product-new-arrivals"),
    path("on-sale/", OnSaleProductsView.as_view(), name="api-product-on-sale"),
    path("<slug:slug>/", ProductDetailView.as_view(), name="api-product-detail"),
]
