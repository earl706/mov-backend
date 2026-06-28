from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BehavioralIntelligenceView,
    DashboardView,
    PatternsView,
    PredictiveScheduleView,
    RetrospectiveViewSet,
    TimelineView,
)

router = DefaultRouter()
router.register("retrospectives", RetrospectiveViewSet, basename="retrospective")

urlpatterns = router.urls + [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("intelligence/behavioral/", BehavioralIntelligenceView.as_view(), name="behavioral"),
    path("intelligence/patterns/", PatternsView.as_view(), name="patterns"),
    path("intelligence/schedule/", PredictiveScheduleView.as_view(), name="schedule"),
    path("intelligence/timeline/", TimelineView.as_view(), name="timeline"),
]
