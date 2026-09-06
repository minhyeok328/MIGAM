from django.contrib import admin
from django.urls import path

from backend.apps.discovery.recommendation_views import InternalRecommendationView
from backend.apps.discovery.views import InternalSearchView
from backend.apps.sources.admin_status import data_status


urlpatterns = [
    path("admin/data-status/", admin.site.admin_view(data_status), name="admin-data-status"),
    path("admin/", admin.site.urls),
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
