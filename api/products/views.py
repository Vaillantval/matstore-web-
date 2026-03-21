from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import StandardResultsPagination
from api.products.filters import ProductFilter
from api.products.serializers import ProductDetailSerializer, ProductListSerializer
from shop.models.Product import Product


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [AllowAny]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "brand"]
    ordering_fields = ["solde_price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Product.objects.filter(is_available=True)
            .prefetch_related("images", "categories", "reviews")
            .order_by("-created_at")
        )

    @extend_schema(
        tags=["Produits"],
        summary="Liste des produits",
        parameters=[
            OpenApiParameter("category", str, description="Slug de la catégorie"),
            OpenApiParameter("min_price", float, description="Prix minimum"),
            OpenApiParameter("max_price", float, description="Prix maximum"),
            OpenApiParameter("in_stock", bool, description="En stock uniquement"),
            OpenApiParameter("search", str, description="Recherche texte"),
            OpenApiParameter("ordering", str, description="Tri: price, -price, created_at"),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Product.objects.prefetch_related("images", "categories", "reviews")

    @extend_schema(tags=["Produits"], summary="Détail d'un produit")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class FeaturedProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Product.objects.filter(is_featured=True, is_available=True)
            .prefetch_related("images", "categories", "reviews")
            .order_by("-created_at")
        )

    @extend_schema(tags=["Produits"], summary="Produits mis en avant")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NewArrivalsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        since = timezone.now() - timedelta(days=30)
        return (
            Product.objects.filter(is_new_arrival=True, is_available=True, created_at__gte=since)
            .prefetch_related("images", "categories", "reviews")
            .order_by("-created_at")
        )

    @extend_schema(tags=["Produits"], summary="Nouveautés (30 derniers jours)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OnSaleProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Product.objects.filter(is_special_offer=True, is_available=True)
            .prefetch_related("images", "categories", "reviews")
            .order_by("-created_at")
        )

    @extend_schema(tags=["Produits"], summary="Produits en promotion")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductSearchView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        from django.db.models import Q
        q = self.request.query_params.get("q", "").strip()
        if not q:
            return Product.objects.none()
        return (
            Product.objects.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(more_description__icontains=q)
                | Q(brand__icontains=q)
                | Q(categories__name__icontains=q),
                is_available=True,
            )
            .prefetch_related("images", "categories", "reviews")
            .distinct()
            .order_by("-created_at")
        )

    @extend_schema(
        tags=["Produits"],
        summary="Recherche full-text de produits",
        parameters=[
            OpenApiParameter("q", str, description="Termes de recherche", required=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response(
                {"success": False, "error": {"code": "MISSING_PARAM", "message": "Le paramètre 'q' est requis."}},
                status=400,
            )
        return super().get(request, *args, **kwargs)
