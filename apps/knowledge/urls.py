from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import GraphView, LinkViewSet, PersonViewSet

router = DefaultRouter()
router.register("people", PersonViewSet, basename="person")
router.register("links", LinkViewSet, basename="link")

urlpatterns = router.urls + [
    path("graph/", GraphView.as_view(), name="knowledge-graph"),
]
