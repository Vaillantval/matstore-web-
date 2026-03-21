from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from api.categories.serializers import CategoryDetailSerializer, CategorySerializer
from shop.models.Category import Category


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.all().order_by("name")

    @extend_schema(tags=["Catégories"], summary="Liste des catégories")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CategoryDetailView(generics.RetrieveAPIView):
    serializer_class = CategoryDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    queryset = Category.objects.all()

    @extend_schema(tags=["Catégories"], summary="Détail catégorie + produits")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
