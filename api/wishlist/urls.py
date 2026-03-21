from django.urls import path

from api.wishlist.views import WishlistAddView, WishlistRemoveView, WishlistView

urlpatterns = [
    path("", WishlistView.as_view(), name="api-wishlist"),
    path("add/", WishlistAddView.as_view(), name="api-wishlist-add"),
    path("remove/<int:pk>/", WishlistRemoveView.as_view(), name="api-wishlist-remove"),
]
