from django.urls import path

from backend.apps.discovery.recommendation_views import InternalRecommendationView
from backend.apps.discovery.views import InternalSearchView


urlpatterns = [
    path(
        "api/internal/v1/recommendations/",
        InternalRecommendationView.as_view(),
        name="internal-recommendations-v1",
    ),
    path(
        "api/internal/v1/search/",
        InternalSearchView.as_view(),
        name="internal-search-v1",
    ),
]
