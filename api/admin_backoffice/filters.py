import django_filters

from shop.models.Order import Order
from shop.models.Product import Product


class AdminOrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    is_paid = django_filters.BooleanFilter()
    payment_method = django_filters.CharFilter(lookup_expr="icontains")
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Order
        fields = ["status", "is_paid", "payment_method", "date_from", "date_to"]


class AdminProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="categories__slug", lookup_expr="iexact")
    is_available = django_filters.BooleanFilter()
    low_stock = django_filters.NumberFilter(field_name="stock", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["category", "is_available", "low_stock"]
