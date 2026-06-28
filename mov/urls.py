"""Root URL configuration for the Mov API.

All feature routers are mounted under /api/. JWT auth lives under /api/auth/.
OpenAPI schema + Swagger UI are served under /api/schema/ and /api/docs/.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.projects.urls")),
    path("", include("apps.tasks.urls")),
    path("", include("apps.habits.urls")),
    path("", include("apps.notes.urls")),
    path("", include("apps.calendarapp.urls")),
    path("", include("apps.focus.urls")),
    path("", include("apps.attachments.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.knowledge.urls")),
    path("", include("apps.analytics.urls")),
    path("", include("apps.search.urls")),
    # Docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]

if settings.STORAGE_BACKEND == "local":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
