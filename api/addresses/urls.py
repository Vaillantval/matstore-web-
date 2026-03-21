from django.urls import path

from api.addresses.views import (
    AddressDetailView,
    AddressListCreateView,
    AddressSetDefaultView,
)

urlpatterns = [
    path("", AddressListCreateView.as_view(), name="api-address-list-create"),
    path("<int:pk>/", AddressDetailView.as_view(), name="api-address-detail"),
    path("<int:pk>/default/", AddressSetDefaultView.as_view(), name="api-address-set-default"),
]
