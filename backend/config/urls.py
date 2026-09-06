from django.contrib import admin
from django.urls import path

from backend.apps.sources.admin_status import data_status
from backend.apps.discovery.artwork_views import InternalArtworkDetailView, InternalArtworkListView

from backend.apps.discovery.detail_views import (
    InternalExhibitionDetailView,
    InternalInstitutionDetailView,
)
from backend.apps.discovery.recommendation_views import InternalRecommendationView
from backend.apps.discovery.views import InternalSearchView


urlpatterns = [
    path("api/internal/v1/artworks/", InternalArtworkListView.as_view(), name="internal-artworks-v1"),
    path("api/internal/v1/artworks/<int:id>/", InternalArtworkDetailView.as_view(), name="internal-artwork-detail-v1"),
    path("admin/data-status/", admin.site.admin_view(data_status), name="admin-data-status"),
    path("admin/", admin.site.urls),
    path(
        "api/internal/v1/exhibitions/<int:id>/",
        InternalExhibitionDetailView.as_view(),
        name="internal-exhibition-detail-v1",
    ),
    path(
        "api/internal/v1/institutions/<int:id>/",
        InternalInstitutionDetailView.as_view(),
        name="internal-institution-detail-v1",
    ),
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
