from rest_framework.routers import DefaultRouter
from .views import TrashedItemViewSet

router = DefaultRouter()
router.register("", TrashedItemViewSet, basename="trash")

urlpatterns = router.urls
