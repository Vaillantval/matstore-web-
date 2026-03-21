from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import ApiError
from api.models import Review
from api.pagination import StandardResultsPagination
from api.permissions import HasVerifiedPurchase, IsOwnerOrAdmin
from api.reviews.serializers import ReviewSerializer
from shop.models.Order import Order
from shop.models.Product import Product


class ReviewListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Avis"],
        parameters=[OpenApiParameter("product", int, description="ID du produit")],
        summary="Liste des avis d'un produit",
    )
    def get(self, request):
        product_id = request.query_params.get("product")
        qs = Review.objects.select_related("author", "product")
        if product_id:
            qs = qs.filter(product_id=product_id)
        qs = qs.order_by("-created_at")

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = ReviewSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["Avis"],
        request=ReviewSerializer,
        responses={201: ReviewSerializer},
        summary="Laisser un avis (achat vérifié requis)",
    )
    def post(self, request):
        product_id = request.data.get("product_id") or request.data.get("product")
        if product_id:
            # Verify purchase
            has_purchase = Order.objects.filter(
                author=request.user,
                status="delivered",
                order_details__product_name__isnull=False,
            ).exists()
            if not has_purchase:
                raise ApiError(
                    "PERMISSION_DENIED",
                    "Vous devez avoir acheté et reçu ce produit pour laisser un avis.",
                )

        serializer = ReviewSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            {"success": True, "data": ReviewSerializer(review, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class ReviewUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, pk, request):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return None
        self.check_object_permissions(request, review)
        return review

    @extend_schema(tags=["Avis"], request=ReviewSerializer, summary="Modifier son avis")
    def patch(self, request, pk):
        review = self.get_object(pk, request)
        if not review:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Avis introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ReviewSerializer(review, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    @extend_schema(tags=["Avis"], summary="Supprimer son avis")
    def delete(self, request, pk):
        review = self.get_object(pk, request)
        if not review:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Avis introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
