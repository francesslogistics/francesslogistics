from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppSettingsView, InquiryViewSet, health_check

router = DefaultRouter()
router.register("inquiries", InquiryViewSet, basename="inquiry")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("settings/", AppSettingsView.as_view(), name="app-settings"),
    path("", include(router.urls)),
]
