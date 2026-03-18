from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                           views.overview,       name='overview'),

    # Profil
    path('account/',                   views.index,          name='account'),
    path('account/save/',              views.save_account,   name='account_save'),
    path('account/password/',          views.reset_user_password, name='account_password'),

    # Adresses
    path('addresses/',                 views.addresses,      name='addresses'),
    path('addresses/create/',          views.address_create, name='address_create'),
    path('addresses/<int:pk>/edit/',   views.address_edit,   name='address_edit'),
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),

    # Commandes
    path('orders/',                    views.orders,         name='orders'),
    path('orders/<int:pk>/',           views.order_detail,   name='order_detail'),
]
