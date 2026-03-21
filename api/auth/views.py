from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from api.auth.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()


@extend_schema(tags=["Auth"])
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        summary="Inscription client",
        description="Crée un nouveau compte client et retourne les tokens JWT directement.",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": RegisterSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        summary="Connexion",
        description="Authentifie l'utilisateur et retourne access + refresh token.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Save fcm_token if provided and the field exists
        fcm_token = serializer.validated_data.get("fcm_token")
        if fcm_token and hasattr(user, "fcm_token"):
            user.fcm_token = fcm_token
            user.save(update_fields=["fcm_token"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
            }
        )


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Déconnexion",
        description="Blackliste le refresh token pour invalider la session.",
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "error": {"code": "MISSING_TOKEN", "message": "refresh token requis."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass
        return Response({"success": True, "message": "Déconnexion réussie."})


@extend_schema(tags=["Auth"])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        summary="Profil utilisateur",
        description="Retourne le profil de l'utilisateur connecté.",
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        summary="Modifier son profil",
    )
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


@extend_schema(tags=["Auth"])
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        summary="Changer son mot de passe",
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"success": True, "message": "Mot de passe modifié avec succès."})


@extend_schema(tags=["Auth"])
class FcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"fcm_token": {"type": "string"}}, "required": ["fcm_token"]}},
        summary="Mettre à jour le FCM token",
        description="Enregistre ou met à jour le token Firebase pour les push notifications Android/iOS.",
    )
    def post(self, request):
        fcm_token = request.data.get("fcm_token", "").strip()
        if not fcm_token:
            return Response(
                {"success": False, "error": {"code": "MISSING_PARAM", "message": "fcm_token est requis."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not hasattr(request.user, "fcm_token"):
            return Response(
                {"success": False, "error": {"code": "NOT_SUPPORTED", "message": "FCM non supporté sur ce serveur."}},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        request.user.fcm_token = fcm_token
        request.user.save(update_fields=["fcm_token"])
        return Response({"success": True, "message": "FCM token enregistré."})
