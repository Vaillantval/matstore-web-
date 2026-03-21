import django_filters
from shop.models.Product import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="categories__slug", lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="solde_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="solde_price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(field_name="is_available")

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "in_stock"]
