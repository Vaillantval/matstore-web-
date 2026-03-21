from django.urls import path, include

urlpatterns = [
    path("auth/", include("api.auth.urls")),
    path("products/", include("api.products.urls")),
    path("categories/", include("api.categories.urls")),
    path("cart/", include("api.cart.urls")),
    path("orders/", include("api.orders.urls")),
    path("payments/", include("api.payments.urls")),
    path("reviews/", include("api.reviews.urls")),
    path("wishlist/", include("api.wishlist.urls")),
    path("addresses/", include("api.addresses.urls")),
    path("admin/", include("api.admin_backoffice.urls")),
]
