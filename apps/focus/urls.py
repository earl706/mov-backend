from rest_framework.routers import DefaultRouter

from .views import FocusSessionViewSet, WorkContextSnapshotViewSet

router = DefaultRouter()
router.register("focus-sessions", FocusSessionViewSet, basename="focussession")
router.register("work-context", WorkContextSnapshotViewSet, basename="workcontext")

urlpatterns = router.urls
