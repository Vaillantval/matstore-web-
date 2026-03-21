from django.urls import path

from api.categories.views import CategoryDetailView, CategoryListView

urlpatterns = [
    path("", CategoryListView.as_view(), name="api-category-list"),
    path("<slug:slug>/", CategoryDetailView.as_view(), name="api-category-detail"),
]
