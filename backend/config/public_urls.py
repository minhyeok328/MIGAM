"""Reuse visitor routes; never register an operator route in the public app."""

from .urls import urlpatterns as internal_patterns

urlpatterns = [route for route in internal_patterns if str(route.pattern).startswith("api/internal/v1/")]
