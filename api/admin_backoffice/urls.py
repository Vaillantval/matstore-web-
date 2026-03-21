from django.urls import path

from api.admin_backoffice.views import (
    AdminCategoryDetailView,
    AdminCategoryListCreateView,
    AdminCustomerDetailView,
    AdminCustomerListView,
    AdminCustomersReportView,
    AdminDashboardView,
    AdminInventoryListView,
    AdminInventoryUpdateView,
    AdminOrderDetailView,
    AdminOrderListView,
    AdminOrderStatusView,
    AdminProductDetailView,
    AdminProductImageUploadView,
    AdminProductListCreateView,
    AdminProductsReportView,
    AdminSalesReportView,
)

urlpatterns = [
    # Dashboard
    path("dashboard/", AdminDashboardView.as_view(), name="api-admin-dashboard"),

    # Products
    path("products/", AdminProductListCreateView.as_view(), name="api-admin-product-list"),
    path("products/<int:pk>/", AdminProductDetailView.as_view(), name="api-admin-product-detail"),
    path("products/<int:pk>/images/", AdminProductImageUploadView.as_view(), name="api-admin-product-images"),

    # Orders
    path("orders/", AdminOrderListView.as_view(), name="api-admin-order-list"),
    path("orders/<int:pk>/", AdminOrderDetailView.as_view(), name="api-admin-order-detail"),
    path("orders/<int:pk>/status/", AdminOrderStatusView.as_view(), name="api-admin-order-status"),

    # Customers
    path("customers/", AdminCustomerListView.as_view(), name="api-admin-customer-list"),
    path("customers/<int:pk>/", AdminCustomerDetailView.as_view(), name="api-admin-customer-detail"),

    # Categories
    path("categories/", AdminCategoryListCreateView.as_view(), name="api-admin-category-list"),
    path("categories/<int:pk>/", AdminCategoryDetailView.as_view(), name="api-admin-category-detail"),

    # Inventory
    path("inventory/", AdminInventoryListView.as_view(), name="api-admin-inventory-list"),
    path("inventory/<int:pk>/", AdminInventoryUpdateView.as_view(), name="api-admin-inventory-update"),

    # Reports
    path("reports/sales/", AdminSalesReportView.as_view(), name="api-admin-report-sales"),
    path("reports/products/", AdminProductsReportView.as_view(), name="api-admin-report-products"),
    path("reports/customers/", AdminCustomersReportView.as_view(), name="api-admin-report-customers"),
]
