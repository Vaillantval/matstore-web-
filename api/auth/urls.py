from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.auth.views import (
    ChangePasswordView,
    FcmTokenView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="api-register"),
    path("login/", LoginView.as_view(), name="api-login"),
    path("logout/", LogoutView.as_view(), name="api-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("me/", MeView.as_view(), name="api-me"),
    path("change-password/", ChangePasswordView.as_view(), name="api-change-password"),
    path("fcm-token/", FcmTokenView.as_view(), name="api-fcm-token"),
]
