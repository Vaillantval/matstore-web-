from django.urls import path

from api.reviews.views import ReviewListCreateView, ReviewUpdateDeleteView

urlpatterns = [
    path("", ReviewListCreateView.as_view(), name="api-review-list-create"),
    path("<int:pk>/", ReviewUpdateDeleteView.as_view(), name="api-review-update-delete"),
]
