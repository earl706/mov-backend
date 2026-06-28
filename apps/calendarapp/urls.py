from rest_framework.routers import DefaultRouter

from .views import CalendarEventViewSet

router = DefaultRouter()
router.register("events", CalendarEventViewSet, basename="event")

urlpatterns = router.urls
