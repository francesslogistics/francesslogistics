from rest_framework.routers import DefaultRouter
from .views import BillingRecordViewSet, QuotationViewSet

billing_router = DefaultRouter()
billing_router.register("", BillingRecordViewSet, basename="billing-record")
billing_urlpatterns = billing_router.urls

quotation_router = DefaultRouter()
quotation_router.register("", QuotationViewSet, basename="quotation")
quotation_urlpatterns = quotation_router.urls

# Back-compat default export — existing `include("billing.urls")` usage
# (the /api/billing/ mount) keeps working unchanged.
urlpatterns = billing_urlpatterns
