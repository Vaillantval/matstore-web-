from django.urls import path

from shop.views.shop_view import index

urlpatterns = [
    path('', index, name='home'),
]
