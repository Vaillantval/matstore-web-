from django.urls import path

from shop.views import checkout_view
from shop.views.payment_view import index as payment_intent_view, payment_success
from shop.views.shop_view import (
    index,
    shop_list,
    product_detail,
    category_view,
    search_view,
    about,
    contact,
    faq,
    terms,
    page_detail,
)
from shop.views.cart_view import (
    cart_detail,
    add_to_cart,
    remove_from_cart,
    update_cart,
    select_carrier,
    wishlist_detail,
    clear_wishlist,
    toggle_wishlist,
)
from shop.views.compare_view import (
    compare_detail,
    add_to_compare,
    remove_from_compare,
)

urlpatterns = [
    path("", index, name="home"),
    path("shop/", shop_list, name="shop_list"),
    path("product/<slug:slug>/", product_detail, name="product_detail"),
    path("category/<slug:slug>/", category_view, name="category"),
    path("search/", search_view, name="search"),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
    path("faq/", faq, name="faq"),
    path("terms/", terms, name="terms"),
    path("page/<slug:slug>/", page_detail, name="page_detail"),
    # Cart
    path("cart/", cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:product_id>/", remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:product_id>/", update_cart, name="update_cart"),
    path("cart/carrier/", select_carrier, name="select_carrier"),
    # Comparaison
    path("comparer/", compare_detail, name="compare"),
    path("comparer/ajouter/<int:product_id>/", add_to_compare, name="add_to_compare"),
    path(
        "comparer/retirer/<int:product_id>/",
        remove_from_compare,
        name="remove_from_compare",
    ),
    # Liste de souhaits
    path("liste-de-souhaits/", wishlist_detail, name="wishlist"),
    path("liste-de-souhaits/vider/", clear_wishlist, name="clear_wishlist"),
    path(
        "liste-de-souhaits/toggle/<int:product_id>/",
        toggle_wishlist,
        name="toggle_wishlist",
    ),
    # Checkout
    path("checkout/", checkout_view.index, name="checkout"),
    path("checkout/add-address/", checkout_view.add_address, name="add_address"),
    path("checkout/login/", checkout_view.login_form, name="login_form"),
    path("create-payment-intent/<int:order_id>/", payment_intent_view, name="create_payment_intent"),
    path("payment-success/", payment_success, name="payment_success"),
]
