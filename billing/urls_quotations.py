"""Separate URL module for /api/quotations/ — kept apart from billing/urls.py
so that include("billing.urls") (used for /api/billing/) and this one don't
collide; they register different viewsets on different routers."""
from .urls import quotation_urlpatterns

urlpatterns = quotation_urlpatterns
