from rest_framework.routers import DefaultRouter

from .views import HabitLogViewSet, HabitViewSet

router = DefaultRouter()
router.register("habits", HabitViewSet, basename="habit")
router.register("habit-logs", HabitLogViewSet, basename="habitlog")

urlpatterns = router.urls
