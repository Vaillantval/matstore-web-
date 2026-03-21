from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import WishlistItem
from api.pagination import StandardResultsPagination
from api.wishlist.serializers import AddToWishlistSerializer, WishlistItemSerializer


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Favoris"], summary="Liste des favoris")
    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related(
            "product"
        ).prefetch_related("product__images", "product__categories")

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(items, request)
        serializer = WishlistItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class WishlistAddView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Favoris"],
        request=AddToWishlistSerializer,
        responses={201: WishlistItemSerializer},
        summary="Ajouter aux favoris",
    )
    def post(self, request):
        serializer = AddToWishlistSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        item = WishlistItem.objects.create(
            user=request.user,
            product=serializer.validated_data["product_id"],
        )
        return Response(
            {"success": True, "data": WishlistItemSerializer(item).data},
            status=status.HTTP_201_CREATED,
        )


class WishlistRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Favoris"], summary="Retirer des favoris")
    def delete(self, request, pk):
        deleted, _ = WishlistItem.objects.filter(pk=pk, user=request.user).delete()
        if not deleted:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Favori introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
