from django.urls import path

from api.orders.views import OrderCancelView, OrderDetailView, OrderListCreateView, OrderTrackingView

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="api-order-list-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="api-order-detail"),
    path("<int:pk>/cancel/", OrderCancelView.as_view(), name="api-order-cancel"),
    path("<int:pk>/track/", OrderTrackingView.as_view(), name="api-order-track"),
]
