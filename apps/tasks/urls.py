from rest_framework.routers import DefaultRouter

from .views import SubtaskViewSet, TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")
router.register("subtasks", SubtaskViewSet, basename="subtask")

urlpatterns = router.urls
