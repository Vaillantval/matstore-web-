from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.addresses.serializers import AddressSerializer
from dashboard.models.Adress import Adress


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Adresses"],
        responses={200: AddressSerializer(many=True)},
        summary="Liste des adresses",
    )
    def get(self, request):
        addresses = Adress.objects.filter(author=request.user).order_by("-created_at")
        return Response({"success": True, "data": AddressSerializer(addresses, many=True).data})

    @extend_schema(
        tags=["Adresses"],
        request=AddressSerializer,
        responses={201: AddressSerializer},
        summary="Ajouter une adresse",
    )
    def post(self, request):
        serializer = AddressSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        addr = serializer.save()
        return Response(
            {"success": True, "data": AddressSerializer(addr).data},
            status=status.HTTP_201_CREATED,
        )


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Adress.objects.get(pk=pk, author=user)
        except Adress.DoesNotExist:
            return None

    @extend_schema(tags=["Adresses"], request=AddressSerializer, summary="Modifier une adresse")
    def patch(self, request, pk):
        addr = self.get_object(pk, request.user)
        if not addr:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Adresse introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AddressSerializer(addr, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    @extend_schema(tags=["Adresses"], summary="Supprimer une adresse")
    def delete(self, request, pk):
        addr = self.get_object(pk, request.user)
        if not addr:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Adresse introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        addr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Adresses"], summary="Définir comme adresse par défaut")
    def patch(self, request, pk):
        try:
            addr = Adress.objects.get(pk=pk, author=request.user)
        except Adress.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Adresse introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(addr, "is_default"):
            Adress.objects.filter(
                author=request.user, adress_type=addr.adress_type
            ).update(is_default=False)
            addr.is_default = True
            addr.save(update_fields=["is_default"])

        return Response({"success": True, "data": AddressSerializer(addr).data})
