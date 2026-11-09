"""
URL configuration for config project.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def api_root(request):
    """Simple landing endpoint so that '/' does not return a 404."""
    return JsonResponse(
        {
            "service": "AI Repository Analyzer API",
            "status": "ok",
            "endpoints": {
                "analyze": "/api/analyze/",
                "repositories": "/api/repositories/",
                "admin": "/admin/",
            },
        }
    )


urlpatterns = [
    path("", api_root, name="api-root"),

    path("admin/", admin.site.urls),

    path("api/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    path("api/", include("api.urls")),
]