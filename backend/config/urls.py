from django.urls import path

from backend.apps.discovery.views import InternalSearchView


urlpatterns = [
    path(
        "api/internal/v1/search/",
        InternalSearchView.as_view(),
        name="internal-search-v1",
    ),
]
