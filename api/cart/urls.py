from django.urls import path

from api.cart.views import CartAddView, CartClearView, CartRemoveView, CartUpdateView, CartView

urlpatterns = [
    path("", CartView.as_view(), name="api-cart"),
    path("add/", CartAddView.as_view(), name="api-cart-add"),
    path("update/<int:item_id>/", CartUpdateView.as_view(), name="api-cart-update"),
    path("remove/<int:item_id>/", CartRemoveView.as_view(), name="api-cart-remove"),
    path("clear/", CartClearView.as_view(), name="api-cart-clear"),
]
